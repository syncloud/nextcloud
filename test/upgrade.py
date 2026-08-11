import base64
import json
import pytest
from subprocess import check_output, run
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.installer import local_install
from syncloudlib.http import wait_for_rest
import requests

TMP_DIR = '/tmp/syncloud'
MARKER_NAME = 'upgrade-marker.txt'
MARKER_BODY = b'pre-store-upgrade-marker'
MAINTENANCE_MARKER = 'syncloud-nextcloud-maintenance'
UPGRADE_FAILED_MARKER = 'syncloud-nextcloud-upgrade-failed'
STORE_VERSION = {}


@pytest.fixture(scope="session")
def module_setup(request, device, artifact_dir):
    def module_teardown():
        device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl > {0}/refresh.journalctl.log'.format(TMP_DIR), throw=False)
        device.run_ssh('snap run nextcloud.occ status > {0}/occ.status.log 2>&1'.format(TMP_DIR), throw=False)
        device.run_ssh('snap run nextcloud.occ group:list > {0}/occ.group.list.log 2>&1'.format(TMP_DIR), throw=False)
        device.scp_from_device('{0}/*'.format(TMP_DIR), artifact_dir)
        run('cp /videos/* {0}'.format(artifact_dir), shell=True)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def test_start(module_setup, app, device_host, domain, device):
    add_host_alias(app, device_host, domain)
    device.activated()
    device.run_ssh('rm -rf {0}'.format(TMP_DIR), throw=False)
    device.run_ssh('mkdir {0}'.format(TMP_DIR), throw=False)


def test_install_store(device):
    device.run_ssh('snap remove nextcloud')
    device.run_ssh('snap install nextcloud', retries=10)


def test_record_store_version(device):
    out = device.run_ssh('snap run nextcloud.occ status --output=json')
    STORE_VERSION['v'] = json.loads(out).get('versionstring')


def test_pre_upgrade_write_marker(app_domain, device_user, device_password):
    r = requests.put(
        'https://{0}/remote.php/webdav/{1}'.format(app_domain, MARKER_NAME),
        data=MARKER_BODY,
        auth=(device_user, device_password),
        verify=False,
    )
    assert r.status_code in (201, 204), r.text


def test_simulate_legacy_admin_rename(device):
    sql = (
        "UPDATE oc_ldap_group_mapping SET owncloud_name='admin' "
        "WHERE owncloud_name='syncloud' AND ldap_dn ILIKE 'cn=syncloud,%';\n"
    )
    b64 = base64.b64encode(sql.encode()).decode()
    device.run_ssh("echo {0} | base64 -d > /tmp/migrate.sql".format(b64))
    out = device.run_ssh(
        "snap run nextcloud.psql -d nextcloud -e -f /tmp/migrate.sql"
    )
    assert 'UPDATE 1' in out, out
    device.run_ssh(
        "snap run nextcloud.occ ldap:set-config s01 ldapAdminGroup admin"
    )


def test_upgrade(device_host, device_password, app_archive_path):
    local_install(device_host, device_password, app_archive_path)


def test_maintenance_page_visible_during_upgrade(device, app_domain, artifact_dir):
    import time
    built = device.run_ssh('grep OC_VersionString /snap/nextcloud/current/nextcloud/version.php')
    store = STORE_VERSION.get('v')
    if store and store in built:
        pytest.skip(
            'store snap is already {0}; a same-version refresh runs no schema '
            'migration, so there is no 503 window to observe'.format(store))
    session = requests.session()
    deadline = time.time() + 1800
    last_status = None
    while time.time() < deadline:
        try:
            r = session.get('https://{0}/'.format(app_domain), verify=False, timeout=10)
            last_status = r.status_code
            if MAINTENANCE_MARKER in r.text:
                with open('{0}/maintenance.page.html'.format(artifact_dir), 'w') as f:
                    f.write(r.text)
                assert r.status_code == 503, r.status_code
                return
        except requests.RequestException:
            pass
        status = json.loads(device.run_ssh('snap run nextcloud.repair-status'))
        if status.get('done'):
            raise AssertionError(
                'repair finished without ever serving the maintenance page, '
                'last status {0}'.format(last_status))
        time.sleep(1)
    raise AssertionError('maintenance page never appeared, last status {0}'.format(last_status))


def test_post_upgrade_repair_status(device):
    import time
    expected_steps = [
        'wait-for-configure',
        'occ-upgrade',
        'maintenance-mode-off',
        'db-add-missing-indices',
        'db-add-missing-columns',
        'db-add-missing-primary-keys',
        'maintenance-repair',
    ]
    deadline = time.time() + 1800
    last = ''
    while time.time() < deadline:
        last = device.run_ssh('snap run nextcloud.repair-status')
        status = json.loads(last)
        if status.get('done'):
            assert status.get('configure_done') is True, last
            steps_by_name = {s['name']: s for s in status.get('steps', [])}
            for name in expected_steps:
                assert name in steps_by_name, 'missing step ' + name + ': ' + last
            for step in status.get('steps', []):
                assert not step.get('error'), 'step ' + step['name'] + ' errored: ' + last
            return
        time.sleep(10)
    raise AssertionError('repair-status never reported done within 30 minutes: ' + last)


def test_post_upgrade_available(app_domain):
    wait_for_rest(requests.session(), "https://{0}".format(app_domain), 200, 10)


def test_status_page_cleared_after_success(device):
    out = device.run_ssh(
        'ls /var/snap/nextcloud/current/syncloud-status.html 2>&1 || true')
    assert 'No such file' in out, out


def test_post_upgrade_marker_survives(app_domain, device_user, device_password):
    r = requests.get(
        'https://{0}/remote.php/webdav/{1}'.format(app_domain, MARKER_NAME),
        auth=(device_user, device_password),
        verify=False,
    )
    assert r.status_code == 200, r.text
    assert r.content == MARKER_BODY


def test_post_upgrade_occ_status(device):
    out = device.run_ssh('snap run nextcloud.occ status --output=json')
    status = json.loads(out)
    assert status.get('installed') is True, out
    assert status.get('maintenance') is False, out


def test_post_upgrade_admin_can_list_users(app_domain, device_user, device_password):
    r = requests.get(
        'https://{0}/ocs/v1.php/cloud/users?format=json'.format(app_domain),
        auth=(device_user, device_password),
        headers={'OCS-APIRequest': 'true'},
        verify=False,
    )
    assert r.status_code == 200, r.text
    meta = r.json()['ocs']['meta']
    assert meta['statuscode'] == 100, r.text


def test_upgrade_failed_page_when_repair_gives_up(device, app_domain):
    import time
    device.run_ssh('snap run nextcloud.occ maintenance:mode --on')
    device.run_ssh('echo 99 > /var/snap/nextcloud/current/.repair-attempts')
    device.run_ssh('touch /var/snap/nextcloud/current/.refresh-needed')
    device.run_ssh('systemctl restart snap.nextcloud.post-start-repair')
    try:
        deadline = time.time() + 180
        body = ''
        while time.time() < deadline:
            r = requests.get('https://{0}/'.format(app_domain), verify=False)
            body = r.text
            if UPGRADE_FAILED_MARKER in body:
                assert r.status_code == 503, r.status_code
                return
            time.sleep(5)
        raise AssertionError('upgrade-failed page never served, last body: ' + body[:500])
    finally:
        device.run_ssh('rm -f /var/snap/nextcloud/current/.repair-attempts', throw=False)
        device.run_ssh('rm -f /var/snap/nextcloud/current/.refresh-needed', throw=False)
        device.run_ssh('rm -f /var/snap/nextcloud/current/syncloud-status.html', throw=False)
        device.run_ssh('snap run nextcloud.occ maintenance:mode --off', throw=False)
        device.run_ssh('systemctl restart snap.nextcloud.post-start-repair', throw=False)
