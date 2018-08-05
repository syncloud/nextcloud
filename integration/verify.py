import json
import os
import sys
from os import listdir
from os.path import dirname, join, exists, abspath, isdir
import time
from subprocess import check_output
import pytest
import shutil

from syncloudlib.integration.loop import loop_device_add, loop_device_cleanup
from syncloudlib.integration.ssh import run_scp, run_ssh
from syncloudlib.integration.installer import local_install, wait_for_sam, wait_for_rest, local_remove, get_platform_data_dir, get_data_dir, get_app_dir, get_service_prefix, get_ssh_env_vars

app_path = join(dirname(__file__), '..')
sys.path.append(join(app_path, 'src'))

lib_path = join(app_path, 'lib')
libs = [abspath(join(lib_path, item)) for item in listdir(lib_path) if isdir(join(lib_path, item))]
map(lambda x: sys.path.append(x), libs)

import requests
from bs4 import BeautifulSoup

SYNCLOUD_INFO = 'syncloud.info'
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
DEFAULT_DEVICE_PASSWORD = 'syncloud'
LOGS_SSH_PASSWORD = DEFAULT_DEVICE_PASSWORD
DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
APP='nextcloud'
TMP_DIR = '/tmp/syncloud'


@pytest.fixture(scope="session")
def platform_data_dir(installer):
    return get_platform_data_dir(installer)
        
@pytest.fixture(scope="session")
def data_dir(installer):
    return get_data_dir(installer, APP)
         

@pytest.fixture(scope="session")
def app_dir(installer):
    return get_app_dir(installer, APP)


@pytest.fixture(scope="session")
def service_prefix(installer):
    return get_service_prefix(installer)


@pytest.fixture(scope="session")
def ssh_env_vars(installer):
    return get_ssh_env_vars(installer, APP)


@pytest.fixture(scope="session")
def module_setup(request, device_host, data_dir, platform_data_dir, app_dir, service_prefix):
    request.addfinalizer(lambda: module_teardown(device_host, data_dir, platform_data_dir, app_dir, service_prefix))


def module_teardown(device_host, data_dir, platform_data_dir, app_dir, service_prefix):
    platform_log_dir = join(LOG_DIR, 'platform_log')
    os.mkdir(platform_log_dir)
    run_scp('root@{0}:{1}/log/* {2}'.format(device_host, platform_data_dir, platform_log_dir), password=LOGS_SSH_PASSWORD, throw=False)
    
    run_scp('root@{0}:/var/log/sam.log {1}'.format(device_host, platform_log_dir), password=LOGS_SSH_PASSWORD, throw=False)

    app_log_dir  = join(LOG_DIR, 'nextcloud_log')
    os.mkdir(app_log_dir )
    run_scp('root@{0}:{1}/log/*.log {2}'.format(device_host, data_dir, app_log_dir), password=LOGS_SSH_PASSWORD, throw=False)

    run_ssh(device_host, 'mkdir {0}'.format(TMP_DIR), password=LOGS_SSH_PASSWORD)
    run_ssh(device_host, 'ls -la {0} > {1}/app.data.ls.log'.format(data_dir, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'ls -la {0}/nextcloud/config > {1}/config.ls.log'.format(data_dir, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'cp {0}/nextcloud/config/config.php {1}'.format(data_dir, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, '{0}/bin/occ-runner > {1}'.format(app_dir, TMP_DIR), password=LOGS_SSH_PASSWORD, env_vars='DATA_DIR={0}'.format(data_dir), throw=False)
    run_ssh(device_host, 'top -bn 1 -w 500 -c > {0}/top.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'ps auxfw > {0}/ps.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'systemctl status {0}nextcloud.php-fpm > {1}/nextcloud.php-fpm.status.log'.format(service_prefix, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'netstat -nlp > {0}/netstat.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'journalctl | tail -500 > {0}/journalctl.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'tail -500 /var/log/syslog > {0}/syslog.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'tail -500 /var/log/messages > {0}/messages.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_ssh(device_host, 'ls -la /snap > {0}/snap.ls.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_ssh(device_host, 'ls -la /snap/nextcloud > {0}/snap.nextcloud.ls.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_ssh(device_host, 'ls -la /var/snap > {0}/var.snap.ls.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_ssh(device_host, 'ls -la /var/snap/nextcloud > {0}/var.snap.nextcloud.ls.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_ssh(device_host, 'ls -la /var/snap/nextcloud/common > {0}/var.snap.nextclouds.common.ls.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_ssh(device_host, 'ls -la /data > {0}/data.ls.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_ssh(device_host, 'ls -la /data/nextcloud > {0}/data.nextcloud.ls.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_scp('root@{0}:{1}/*.log {2}'.format(device_host, TMP_DIR, app_log_dir), password=LOGS_SSH_PASSWORD, throw=False)
    

@pytest.fixture(scope='function')
def syncloud_session(device_host):
    session = requests.session()
    session.post('https://{0}/rest/login'.format(device_host), data={'name': DEVICE_USER, 'password': DEVICE_PASSWORD}, verify=False)
    return session


@pytest.fixture(scope='function')
def nextcloud_session_domain(user_domain, device_host):
    session = requests.session()
    response = session.get('https://{0}/index.php/login'.format(device_host), headers={"Host": user_domain}, allow_redirects=False, verify=False)
    print(response.text.encode("UTF-8"))
    print(response.headers)
    soup = BeautifulSoup(response.text, "html.parser")
    requesttoken = soup.find_all('input', {'name': 'requesttoken'})[0]['value']
    response = session.post('https://{0}/index.php/login'.format(device_host),
                            headers={"Host": user_domain},
                            data={'user': DEVICE_USER, 'password': DEVICE_PASSWORD, 'requesttoken': requesttoken},
                            allow_redirects=False, verify=False)
    assert response.status_code == 303, response.text
    return session, requesttoken


def test_start(module_setup):
    shutil.rmtree(LOG_DIR, ignore_errors=True)
    os.mkdir(LOG_DIR)


def test_activate_device(auth, device_host):
    email, password, domain, release = auth

    response = requests.post('http://{0}:81/rest/activate'.format(device_host),
                             data={'main_domain': SYNCLOUD_INFO, 'redirect_email': email, 'redirect_password': password,
                                   'user_domain': domain, 'device_username': DEVICE_USER, 'device_password': DEVICE_PASSWORD}, verify=False)
    assert response.status_code == 200, response.text
    global LOGS_SSH_PASSWORD
    LOGS_SSH_PASSWORD = DEVICE_PASSWORD


#def test_occ(device_host, app_dir, data_dir):
#    run_ssh(device_host, '{0}/bin/occ-runner help maintenance:install'.format(app_dir), password=LOGS_SSH_PASSWORD, env_vars='DATA_DIR={0}'.format(data_dir))

def test_install(app_archive_path, device_host, installer):
    local_install(device_host, DEVICE_PASSWORD, app_archive_path, installer)


def test_resource(nextcloud_session_domain, user_domain, device_host):
    session, _ = nextcloud_session_domain
    response = session.get('https://{0}/core/img/loading.gif'.format(device_host), headers={"Host": user_domain}, verify=False)
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("megabytes", [1, 300])
def test_sync(user_domain, megabytes, device_host, app_dir, data_dir):

    sync_file = 'test.file-{0}'.format(megabytes)
    if os.path.isfile(sync_file):
        os.remove(sync_file)
    print(check_output('dd if=/dev/zero of={0} count={1} bs=1M'.format(sync_file, megabytes), shell=True))
    print(check_output(webdav_upload(DEVICE_USER, DEVICE_PASSWORD, sync_file, sync_file, user_domain), shell=True))

    sync_file_download = 'test.file.download'
    if os.path.isfile(sync_file_download):
        os.remove(sync_file_download)
    print(check_output(webdav_download(DEVICE_USER, DEVICE_PASSWORD, sync_file, sync_file_download, user_domain), shell=True))

    assert os.path.isfile(sync_file_download)
    run_ssh(device_host, 'rm /data/nextcloud/{0}/files/{1}'.format(DEVICE_USER, sync_file), password=DEVICE_PASSWORD)
    files_scan(device_host, app_dir, data_dir)


def webdav_upload(user, password, file_from, file_to, user_domain):
    return 'curl -k -T {2} https://{0}:{1}@{4}/remote.php/webdav/{3}'.format(user, password, file_from, file_to, user_domain)


def webdav_download(user, password, file_from, file_to, user_domain):
    return 'curl -k -o {3} https://{0}:{1}@{4}/remote.php/webdav/{2}'.format(user, password, file_from, file_to, user_domain)


def files_scan(device_host, app_dir, data_dir):
    run_ssh(device_host, '{0}/bin/occ-runner files:scan --all'.format(app_dir), password=DEVICE_PASSWORD, env_vars='DATA_DIR={0}'.format(data_dir))


def test_occ(device_host, app_dir, data_dir):
    run_ssh(device_host, '{0}/bin/occ-runner'.format(app_dir), password=DEVICE_PASSWORD, env_vars='DATA_DIR={0}'.format(data_dir))


def test_visible_through_platform(user_domain, device_host):
    response = requests.get('https://{0}/index.php/login'.format(device_host), headers={"Host": user_domain}, allow_redirects=False, verify=False)
    assert response.status_code == 200, response.text


def test_admin(nextcloud_session_domain, user_domain, device_host):
    session, _ = nextcloud_session_domain
    response = session.get('https://{0}/index.php/settings/admin'.format(device_host), headers={"Host": user_domain}, allow_redirects=False, verify=False)
    assert response.status_code == 200, response.text


def test_verification(nextcloud_session_domain, user_domain):
    session, _ = nextcloud_session_domain
    response = session.get('https://{0}/index.php/settings/integrity/failed'.format(user_domain), allow_redirects=False, verify=False)
    print(response.text)
    assert response.status_code == 200, response.text
    assert 'INVALID_HASH' not in response.text
    assert 'EXCEPTION' not in response.text


def test_disk(syncloud_session, user_domain, device_host, app_dir, data_dir):

    loop_device_cleanup(device_host, '/tmp/test0', DEVICE_PASSWORD)
    loop_device_cleanup(device_host, '/tmp/test1', DEVICE_PASSWORD)

    device0 = loop_device_add(device_host, 'ext4', '/tmp/test0', DEVICE_PASSWORD)
    __activate_disk(syncloud_session, device0, device_host, app_dir, data_dir)
    __create_test_dir('test0', user_domain, device_host)
    __check_test_dir(nextcloud_session_domain(user_domain, device_host), 'test0', user_domain, device_host)

    device1 = loop_device_add(device_host, 'ext2', '/tmp/test1', DEVICE_PASSWORD)
    __activate_disk(syncloud_session, device1, device_host, app_dir, data_dir)
    __create_test_dir('test1', user_domain, device_host)
    __check_test_dir(nextcloud_session_domain(user_domain, device_host), 'test1', user_domain, device_host)

    __activate_disk(syncloud_session, device0, device_host, app_dir, data_dir)
    __check_test_dir(nextcloud_session_domain(user_domain, device_host), 'test0', user_domain, device_host)

    __deactivate_disk(syncloud_session, device_host, app_dir, data_dir)
  

def __log_data_dir(device_host):
    run_ssh(device_host, 'ls -la /data', password=DEVICE_PASSWORD)
    run_ssh(device_host, 'mount', password=DEVICE_PASSWORD)
    run_ssh(device_host, 'ls -la /data/', password=DEVICE_PASSWORD)
    run_ssh(device_host, 'ls -la /data/nextcloud', password=DEVICE_PASSWORD)


def __activate_disk(syncloud_session, loop_device, device_host, app_dir, data_dir):

    __log_data_dir(device_host)
    response = syncloud_session.get('https://{0}/rest/settings/disk_activate'.format(device_host),
                                    params={'device': loop_device}, allow_redirects=False)
    __log_data_dir(device_host)
    files_scan(device_host, app_dir, data_dir)
    assert response.status_code == 200, response.text


def __deactivate_disk(syncloud_session, device_host, app_dir, data_dir):

    response = syncloud_session.get('https://{0}/rest/settings/disk_deactivate'.format(device_host),
                                    allow_redirects=False)
    files_scan(device_host, app_dir, data_dir)
    assert response.status_code == 200, response.text


def __create_test_dir(test_dir, user_domain, device_host):
    response = requests.request('MKCOL', 'https://{0}:{1}@{2}/remote.php/webdav/{3}'.format(
        DEVICE_USER, DEVICE_PASSWORD, device_host, test_dir),
                                headers={"Host": user_domain}, verify=False)
    print(response.text)
    assert response.status_code == 201, response.text


def __check_test_dir(nextcloud_session, test_dir, user_domain, device_host):

    response = requests.get('https://{0}'.format(device_host), headers={"Host": user_domain}, verify=False)
    assert response.status_code == 200, BeautifulSoup(response.text, "html.parser").find('li', class_='error')

    nextcloud, _ = nextcloud_session
    response = nextcloud.get('https://{0}/index.php/apps/files/ajax/list.php?dir=/'.format(device_host),
                             headers={"Host": user_domain},
                             allow_redirects=False)
    info = json.loads(response.text)
    print(response.text)
    dirs = map(lambda v: v['name'], info['data']['files'])
    assert test_dir in dirs, response.text


def test_phpinfo(device_host, app_dir, data_dir):
    run_ssh(device_host, '{0}/bin/php-runner -i > {1}/log/phpinfo.log'.format(app_dir, data_dir),
            password=DEVICE_PASSWORD, env_vars='DATA_DIR={0}'.format(data_dir))


def test_remove(syncloud_session, device_host):
    response = syncloud_session.get('https://{0}/rest/remove?app_id=nextcloud'.format(device_host),
                                    allow_redirects=False, verify=False)
    assert response.status_code == 200, response.text
    wait_for_sam(device_host, syncloud_session)


def test_reinstall(app_archive_path, device_host, installer):
    local_install(device_host, DEVICE_PASSWORD, app_archive_path, installer)
