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


def test_pre_upgrade_write_marker(app_domain, device_user, device_password):
    r = requests.put(
        'https://{0}/remote.php/webdav/{1}'.format(app_domain, MARKER_NAME),
        data=MARKER_BODY,
        auth=(device_user, device_password),
        verify=False,
    )
    assert r.status_code in (201, 204), r.text


def test_upgrade(device_host, device_password, app_archive_path, app_domain):
    local_install(device_host, device_password, app_archive_path)
    wait_for_rest(requests.session(), "https://{0}".format(app_domain), 200, 10)


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
