import json
import os
from os.path import join
from subprocess import check_output
import shutil

import pytest
import requests
from bs4 import BeautifulSoup
from syncloudlib.integration.installer import local_install, wait_for_installer
from syncloudlib.integration.loop import loop_device_add, loop_device_cleanup
from syncloudlib.integration.hosts import add_host_alias

TMP_DIR = '/tmp/syncloud'


@pytest.fixture(scope="session")
def module_setup(request, device, data_dir, platform_data_dir, app_dir, service_prefix, log_dir):
    def module_teardown():
        platform_log_dir = join(log_dir, 'platform_log')
        os.mkdir(platform_log_dir)
        device.scp_from_device('{0}/log/*'.format(platform_data_dir), platform_log_dir)
        device.run_ssh('ls -la {0} > {1}/app.data.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/nextcloud/config > {1}/config.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('cp {0}/nextcloud/config/config.php {1}'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('snap run nextcloud.occ > {1}/occ.help.log'.format(app_dir, TMP_DIR), throw=False)
        device.run_ssh('top -bn 1 -w 500 -c > {0}/top.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ps auxfw > {0}/ps.log'.format(TMP_DIR), throw=False)
        device.run_ssh('systemctl status {0}nextcloud.php-fpm > {1}/nextcloud.php-fpm.status.log'.format(service_prefix, TMP_DIR), throw=False)
        device.run_ssh('netstat -nlp > {0}/netstat.log'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl | tail -500 > {0}/journalctl.log'.format(TMP_DIR), throw=False)
        device.run_ssh('tail -500 /var/log/syslog > {0}/syslog.log'.format(TMP_DIR), throw=False)
        device.run_ssh('tail -500 /var/log/messages > {0}/messages.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /snap > {0}/snap.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /snap/nextcloud > {0}/snap.nextcloud.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /var/snap > {0}/var.snap.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /var/snap/nextcloud > {0}/var.snap.nextcloud.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /var/snap/nextcloud/common > {0}/var.snap.nextcloud.common.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /data > {0}/data.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /data/nextcloud > {0}/data.nextcloud.ls.log'.format(TMP_DIR), throw=False)

        app_log_dir = join(log_dir, 'log')
        os.mkdir(app_log_dir)
        device.scp_from_device('{0}/log/*.log'.format(data_dir), app_log_dir)
        device.scp_from_device('{0}/*'.format(TMP_DIR), app_log_dir)

    request.addfinalizer(module_teardown)


@pytest.fixture(scope='function')
def nextcloud_session_domain(app_domain, device_user, device_password):
    session = requests.session()
    response = session.get('https://{0}/index.php/login'.format(app_domain), allow_redirects=False, verify=False)
    print(response.text.encode("UTF-8"))
    print(response.headers)
    soup = BeautifulSoup(response.text, "html.parser")
    requesttoken = soup.find_all('input', {'name': 'requesttoken'})[0]['value']
    response = session.post('https://{0}/index.php/login'.format(app_domain),
                            data={'user': device_user, 'password': device_password, 'requesttoken': requesttoken},
                            allow_redirects=False, verify=False)
    assert response.status_code == 303, response.text
    return session, requesttoken


def test_start(module_setup, device, device_host, app, log_dir, domain):
    shutil.rmtree(log_dir, ignore_errors=True)
    os.mkdir(log_dir)
    add_host_alias(app, device_host, domain)
    device.run_ssh('date', retries=100)
    device.run_ssh('mkdir {0}'.format(TMP_DIR))


def test_activate_device(device):
    response = device.activate()
    assert response.status_code == 200, response.text


def test_install(app_archive_path, device_session, device_host, device_password):
    local_install(device_host, device_password, app_archive_path)
    wait_for_installer(device_session, device_host)


def test_resource(nextcloud_session_domain, app_domain):
    session, _ = nextcloud_session_domain
    response = session.get('https://{0}/core/img/loading.gif'.format(app_domain), verify=False)
    assert response.status_code == 200, response.text


def test_index(nextcloud_session_domain, app_domain, log_dir):
    session, _ = nextcloud_session_domain
    response = session.get('https://{0}'.format(app_domain), verify=False)
    with open(join(log_dir, 'index.log'), 'w') as f:
        f.write(response.text.encode("UTF-8"))
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("megabytes", [1, 300])
def test_sync(app_domain, megabytes, device, device_user, device_password):
    sync_file = 'test.file-{0}'.format(megabytes)
    if os.path.isfile(sync_file):
        os.remove(sync_file)
    print(check_output('dd if=/dev/zero of={0} count={1} bs=1M'.format(sync_file, megabytes), shell=True))
    print(check_output(webdav_upload(device_user, device_password, sync_file, sync_file, app_domain), shell=True))

    sync_file_download = 'test.file.download'
    if os.path.isfile(sync_file_download):
        os.remove(sync_file_download)
    print(check_output(webdav_download(device_user, device_password, sync_file, sync_file_download, app_domain),
                       shell=True))

    assert os.path.isfile(sync_file_download)
    device.run_ssh('rm /data/nextcloud/{0}/files/{1}'.format(device_user, sync_file))
    files_scan(device)


def webdav_upload(user, password, file_from, file_to, app_domain):
    return 'curl -k -T {2} https://{0}:{1}@{4}/remote.php/webdav/{3}'.format(user, password, file_from, file_to,
                                                                             app_domain)


def webdav_download(user, password, file_from, file_to, app_domain):
    return 'curl -k -o {3} https://{0}:{1}@{4}/remote.php/webdav/{2}'.format(user, password, file_from, file_to,
                                                                             app_domain)


def files_scan(device):
    device.run_ssh('snap run nextcloud.occ files:scan --all')


def test_occ(device):
    device.run_ssh('snap run nextcloud.occ')


def test_cron(device):
    device.run_ssh('snap run nextcloud.cron')


def test_visible_through_platform(app_domain):
    response = requests.get('https://{0}/index.php/login'.format(app_domain), allow_redirects=False, verify=False)
    assert response.status_code == 200, response.text


def test_carddav(nextcloud_session_domain, app_domain, log_dir):
    session, _ = nextcloud_session_domain
    response = session.request('PROPFIND', 'https://{0}/.well-known/carddav'.format(app_domain), allow_redirects=True,
                               verify=False)
    with open(join(log_dir, 'well-known.carddav.headers.log'), 'w') as f:
        f.write(str(response.headers).replace(',', '\n'))


def test_caldav(nextcloud_session_domain, app_domain, log_dir):
    session, _ = nextcloud_session_domain
    response = session.request('PROPFIND', 'https://{0}/.well-known/caldav'.format(app_domain), allow_redirects=True,
                               verify=False)
    with open(join(log_dir, 'well-known.caldav.headers.log'), 'w') as f:
        f.write(str(response.headers).replace(',', '\n'))


def test_admin(nextcloud_session_domain, app_domain, log_dir):
    session, _ = nextcloud_session_domain
    response = session.get('https://{0}/index.php/settings/admin'.format(app_domain), allow_redirects=False,
                           verify=False)
    with open(join(log_dir, 'admin.log'), 'w') as f:
        f.write(response.text.encode("UTF-8"))
    assert response.status_code == 200, response.text


def test_verification(nextcloud_session_domain, app_domain, log_dir):
    session, _ = nextcloud_session_domain
    response = session.get('https://{0}/index.php/settings/integrity/failed'.format(app_domain), allow_redirects=False,
                           verify=False)
    with open(join(log_dir, 'integrity.failed.log'), 'w') as f:
        f.write(response.text)
    assert response.status_code == 200, response.text
    assert 'INVALID_HASH' not in response.text
    assert 'EXCEPTION' not in response.text


def test_disk(device_session, app_domain, device_host, device_user, device_password):
    loop_device_cleanup(device_host, '/tmp/test0', device_password)
    loop_device_cleanup(device_host, '/tmp/test1', device_password)

    device0 = loop_device_add(device_host, 'ext4', '/tmp/test0', device_password)
    __activate_disk(device_session, device0, device, device_host)
    __create_test_dir('test0', app_domain, device_host, device_user, device_password)
    __check_test_dir(nextcloud_session_domain(app_domain, device_user, device_password), 'test0', app_domain)

    device1 = loop_device_add(device_host, 'ext2', '/tmp/test1', device_password)
    __activate_disk(device_session, device1, device, device_host)
    __create_test_dir('test1', app_domain, device_host, device_user, device_password)
    __check_test_dir(nextcloud_session_domain(app_domain, device_user, device_password), 'test1', app_domain)

    __activate_disk(device_session, device0, device, device_host, device_password)
    __check_test_dir(nextcloud_session_domain(app_domain, device_user, device_password), 'test0', app_domain)

    __deactivate_disk(device_session, device, device_host, device_password)


def __log_data_dir(device):
    device.run_ssh('ls -la /data')
    device.run_ssh('mount')
    device.run_ssh('ls -la /data/')
    device.run_ssh('ls -la /data/nextcloud')


def __activate_disk(device_session, loop_device, device, device_host):
    __log_data_dir(device)
    response = device_session.get('https://{0}/rest/settings/disk_activate'.format(device_host),
                                  params={'device': loop_device}, allow_redirects=False)
    __log_data_dir(device)
    files_scan(device)
    assert response.status_code == 200, response.text


def __deactivate_disk(device_session, device, device_host):
    response = device_session.get('https://{0}/rest/settings/disk_deactivate'.format(device_host),
                                  allow_redirects=False)
    files_scan(device)
    assert response.status_code == 200, response.text


def __create_test_dir(test_dir, app_domain, device_host, device_user, device_password):
    response = requests.request('MKCOL', 'https://{0}:{1}@{2}/remote.php/webdav/{3}'.format(
        device_user, device_password, device_host, test_dir),
                                headers={"Host": app_domain}, verify=False)
    print(response.text)
    assert response.status_code == 201, response.text


def __check_test_dir(nextcloud_session, test_dir, app_domain):
    response = requests.get('https://{0}'.format(app_domain), verify=False)
    assert response.status_code == 200, BeautifulSoup(response.text, "html.parser").find('li', class_='error')

    nextcloud, _ = nextcloud_session
    response = nextcloud.get('https://{0}/index.php/apps/files/ajax/list.php?dir=/'.format(app_domain),
                             verify=False,
                             allow_redirects=False)
    info = json.loads(response.text)
    print(response.text)
    dirs = map(lambda v: v['name'], info['data']['files'])
    assert test_dir in dirs, response.text


def test_phpinfo(device):
    device.run_ssh('snap run nextcloud.php -i > {0}/phpinfo.log'.format(TMP_DIR))


def test_storage_change_event(device):
    device.run_ssh('/snap/platform/current/python/bin/python '
                         '/snap/nextcloud/current/hooks/storage-change.py '
                         '> {0}/storage-change.log'.format(TMP_DIR))


def test_access_change_event(device):
    device.run_ssh('/snap/platform/current/python/bin/python '
                         '/snap/nextcloud/current/hooks/access-change.py '
                         '> {0}/access-change.log'.format(TMP_DIR))


def test_remove(device_session, device_host):
    response = device_session.get('https://{0}/rest/remove?app_id=nextcloud'.format(device_host),
                                  allow_redirects=False, verify=False)
    assert response.status_code == 200, response.text
    wait_for_installer(device_session, device_host)


def test_reinstall(app_archive_path, device_host, device_password):
    local_install(device_host, device_password, app_archive_path)


def test_upgrade(app_archive_path, device_host, device_password):
    local_install(device_host, device_password, app_archive_path)
