import json
import os
from os.path import join
from subprocess import check_output
import shutil
from requests.auth import HTTPBasicAuth
import pytest
import requests
from bs4 import BeautifulSoup
from syncloudlib.integration.installer import local_install, wait_for_installer
from syncloudlib.integration.loop import loop_device_add, loop_device_cleanup
from syncloudlib.integration.hosts import add_host_alias_by_ip
from requests.packages.urllib3.exceptions import InsecureRequestWarning

TMP_DIR = '/tmp/syncloud'

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


@pytest.fixture(scope="session")
def module_setup(request, device, platform_data_dir, app_dir, artifact_dir):
    def module_teardown():
        platform_log_dir = join(artifact_dir, 'platform_log')
        os.mkdir(platform_log_dir)
        device.scp_from_device('{0}/log/*'.format(platform_data_dir), platform_log_dir)
        device.run_ssh('ls -la /var/snap/nextcloud/current > {0}/app.data.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /var/snap/nextcloud/current/nextcloud/config > {0}/config.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('cp /var/snap/nextcloud/current/nextcloud/config/config.php {0}'.format(TMP_DIR), throw=False)
        device.run_ssh('snap run nextcloud.occ > {1}/occ.help.log'.format(app_dir, TMP_DIR), throw=False)
        device.run_ssh('top -bn 1 -w 500 -c > {0}/top.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ps auxfw > {0}/ps.log'.format(TMP_DIR), throw=False)
        device.run_ssh('systemctl status snap.nextcloud.php-fpm > {0}/nextcloud.php-fpm.status.log'.format(TMP_DIR),
                       throw=False)
        device.run_ssh('netstat -nlp > {0}/netstat.log'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl | tail -500 > {0}/journalctl.log'.format(TMP_DIR), throw=False)
        device.run_ssh('tail -500 /var/log/syslog > {0}/syslog.log'.format(TMP_DIR), throw=False)
        device.run_ssh('tail -500 /var/log/messages > {0}/messages.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /snap > {0}/snap.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /snap/nextcloud > {0}/snap.nextcloud.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /var/snap > {0}/var.snap.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /var/snap/nextcloud > {0}/var.snap.nextcloud.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /var/snap/nextcloud/common > {0}/var.snap.nextcloud.common.ls.log'.format(TMP_DIR),
                       throw=False)
        device.run_ssh('ls -la /data > {0}/data.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /data/nextcloud > {0}/data.nextcloud.ls.log'.format(TMP_DIR), throw=False)

        app_log_dir = join(artifact_dir, 'log')
        os.mkdir(app_log_dir)
        device.scp_from_device('/var/snap/nextcloud/common/log/*.log', app_log_dir)
        device.scp_from_device('{0}/*'.format(TMP_DIR), app_log_dir)
        shutil.copy2('/etc/hosts', app_log_dir)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def test_start(module_setup, device, device_host, app, domain):
    add_host_alias_by_ip(app, domain, device_host)
    device.run_ssh('date', retries=100)
    device.run_ssh('mkdir {0}'.format(TMP_DIR))


def test_activate_device(device):
    response = device.activate()
    assert response.status_code == 200, response.text


def test_install(app_archive_path, device_session, device_host, device_password):
    local_install(device_host, device_password, app_archive_path)
    wait_for_installer(device_session, device_host)


# noinspection PyUnresolvedReferences
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
    response = requests.get('https://{0}/login'.format(app_domain), allow_redirects=False, verify=False)
    assert response.status_code == 200, response.text


def test_occ_users(device):
    device.run_ssh('snap run nextcloud.occ user:list')


def test_occ_check(device):
    device.run_ssh('snap run nextcloud.occ check')


def test_occ_status(device):
    device.run_ssh('snap run nextcloud.occ status   ')


def test_webdav(app_domain, artifact_dir, device_user, device_password):
    response = requests.request('PROPFIND', 'https://{0}:{1}@{2}/remote.php/webdav/'.format(
        device_user, device_password, app_domain), verify=False)
    with open(join(artifact_dir, 'webdav.list.log'), 'w') as f:
        f.write(str(response.text).replace(',', '\n'))


def test_carddav(app_domain, artifact_dir, device_user, device_password):
    response = requests.request(
        'PROPFIND',
        'https://{0}/.well-known/carddav'.format(app_domain),
        allow_redirects=True,
        verify=False,
        auth=HTTPBasicAuth(device_user, device_password))
    with open(join(artifact_dir, 'well-known.carddav.headers.log'), 'w') as f:
        f.write(str(response.headers).replace(',', '\n'))


def test_caldav(app_domain, artifact_dir, device_user, device_password):
    response = requests.request(
        'PROPFIND',
        'https://{0}/.well-known/caldav'.format(app_domain),
        allow_redirects=True,
        verify=False,
        auth=HTTPBasicAuth(device_user, device_password))
    with open(join(artifact_dir, 'well-known.caldav.headers.log'), 'w') as f:
        f.write(str(response.headers).replace(',', '\n'))


def test_disk(device_session, app_domain, device, device_host, device_user, device_password, artifact_dir):
    loop_device_cleanup(device_host, '/tmp/test0', device_password)
    loop_device_cleanup(device_host, '/tmp/test1', device_password)

    __create_test_dir('test00', app_domain, device_user, device_password, artifact_dir)
    files_scan(device)
    __check_test_dir(device_user, device_password, 'test00', app_domain, artifact_dir)

    device0 = loop_device_add(device_host, 'ext4', '/tmp/test0', device_password)
    __activate_disk(device_session, device0, device, device_host)
    __create_test_dir('test0', app_domain, device_user, device_password, artifact_dir)
    __check_test_dir(device_user, device_password, 'test0', app_domain, artifact_dir)

    device1 = loop_device_add(device_host, 'ext2', '/tmp/test1', device_password)
    __activate_disk(device_session, device1, device, device_host)
    __create_test_dir('test1', app_domain, device_user, device_password, artifact_dir)
    __check_test_dir(device_user, device_password, 'test1', app_domain, artifact_dir)

    __activate_disk(device_session, device0, device, device_host)
    __check_test_dir(device_user, device_password, 'test0', app_domain, artifact_dir)

    __deactivate_disk(device_session, device, device_host)


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

    device.run_ssh('snap run nextcloud.occ > {0}/occ.activate.log'.format(TMP_DIR))

def __deactivate_disk(device_session, device, device_host):
    response = device_session.get('https://{0}/rest/settings/disk_deactivate'.format(device_host),
                                  allow_redirects=False)
    files_scan(device)
    assert response.status_code == 200, response.text


def __create_test_dir(test_dir, app_domain, device_user, device_password, artifact_dir):
    response = requests.request('MKCOL', 'https://{0}:{1}@{2}/remote.php/webdav/{3}'.format(
        device_user, device_password, app_domain, test_dir), verify=False)
    with open(join(artifact_dir, 'create.{0}.dir.log'.format(test_dir)), 'w') as f:
        f.write(response.text)
    assert response.status_code == 201, response.text


def __check_test_dir(device_user, device_password, test_dir, app_domain, artifact_dir):
    response = requests.request('PROPFIND', 'https://{0}:{1}@{2}/remote.php/webdav/'.format(
        device_user, device_password, app_domain), verify=False)
    info = BeautifulSoup(response.text, "xml")
    with open(join(artifact_dir, 'check.{0}.dir.log'.format(test_dir)), 'w') as f:
        f.write(response.text)
    #dirs = map(lambda v: v['name'], info['data']['files'])
    assert test_dir in response.text, response.text


def test_phpinfo(device):
    device.run_ssh('snap run nextcloud.php -i > {0}/phpinfo.log'.format(TMP_DIR))


def test_storage_change_event(device):
    device.run_ssh('snap run nextcloud.storage-change > {0}/storage-change.log'.format(TMP_DIR))


def test_access_change_event(device):
    device.run_ssh('snap run nextcloud.access-change > {0}/access-change.log'.format(TMP_DIR))


def test_remove(device_session, device_host):
    response = device_session.get('https://{0}/rest/remove?app_id=nextcloud'.format(device_host),
                                  allow_redirects=False, verify=False)
    assert response.status_code == 200, response.text
    wait_for_installer(device_session, device_host)


def test_reinstall(app_archive_path, device_host, device_password):
    local_install(device_host, device_password, app_archive_path)


def test_upgrade(app_archive_path, device_host, device_password):
    local_install(device_host, device_password, app_archive_path)
