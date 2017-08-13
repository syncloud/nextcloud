import json
import os
import sys
from os import listdir
from os.path import dirname, join, exists, abspath, isdir
import time
from subprocess import check_output
import pytest
import shutil

from integration.util.loop import loop_device_add, loop_device_cleanup
from integration.util.ssh import run_scp, run_ssh

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


@pytest.fixture(scope="session")
def module_setup(request, device_host):
    request.addfinalizer(lambda: module_teardown(device_host))


def module_teardown(device_host):
    platform_log_dir = join(LOG_DIR, 'platform_log')
    os.mkdir(platform_log_dir)
    run_scp('root@{0}:/opt/data/platform/log/* {1}'.format(device_host, platform_log_dir), password=LOGS_SSH_PASSWORD)
    
    run_scp('root@{0}:/var/log/sam.log {1}'.format(device_host, platform_log_dir), password=LOGS_SSH_PASSWORD)

    print('systemd logs')
    run_ssh(device_host, 'journalctl | tail -200', password=LOGS_SSH_PASSWORD)

    app_log_dir  = join(LOG_DIR, 'nextcloud_log')
    os.mkdir(app_log_dir )
    run_scp('root@{0}:/opt/data/nextcloud/log/*.log {1}'.format(device_host, app_log_dir ), password=LOGS_SSH_PASSWORD)

    

@pytest.fixture(scope='function')
def syncloud_session(device_host):
    session = requests.session()
    session.post('http://{0}/rest/login'.format(device_host), data={'name': DEVICE_USER, 'password': DEVICE_PASSWORD})
    return session


@pytest.fixture(scope='function')
def nextcloud_session_domain(user_domain, device_host):
    session = requests.session()
    response = session.get('http://{0}/index.php/login'.format(device_host), headers={"Host": user_domain}, allow_redirects=False)
    #print(response.text)
    soup = BeautifulSoup(response.text, "html.parser")
    requesttoken = soup.find_all('input', {'name': 'requesttoken'})[0]['value']
    response = session.post('http://{0}/index.php/login'.format(device_host),
                            headers={"Host": user_domain},
                            data={'user': DEVICE_USER, 'password': DEVICE_PASSWORD, 'requesttoken': requesttoken},
                            allow_redirects=False)
    assert response.status_code == 303, response.text
    return session, requesttoken


def test_start(module_setup):
    shutil.rmtree(LOG_DIR, ignore_errors=True)
    os.mkdir(LOG_DIR)


def test_activate_device(auth, device_host):
    email, password, domain, release = auth

    run_ssh(device_host, '/opt/app/sam/bin/sam update --release {0}'.format(release), password=DEFAULT_DEVICE_PASSWORD)
    run_ssh(device_host, '/opt/app/sam/bin/sam --debug upgrade platform', password=DEFAULT_DEVICE_PASSWORD)

    response = requests.post('http://{0}:81/rest/activate'.format(device_host),
                             data={'main_domain': SYNCLOUD_INFO, 'redirect_email': email, 'redirect_password': password,
                                   'user_domain': domain, 'device_username': DEVICE_USER, 'device_password': DEVICE_PASSWORD})
    assert response.status_code == 200, response.text
    global LOGS_SSH_PASSWORD
    LOGS_SSH_PASSWORD = DEVICE_PASSWORD


# def test_enable_external_access(syncloud_session, device_host):
#     response = syncloud_session.get('http://{0}/server/rest/settings/set_protocol'.format(device_host), params={'protocol': 'https'})
#     assert '"success": true' in response.text
#     assert response.status_code == 200


def test_install(app_archive_path, device_host):
    __local_install(app_archive_path, device_host)


def test_resource(nextcloud_session_domain, user_domain, device_host):
    session, _ = nextcloud_session_domain
    response = session.get('http://{0}/core/img/loading.gif'.format(device_host), headers={"Host": user_domain})
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("megabytes", [1, 300])
def test_sync(user_domain, megabytes, device_host):

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
    files_scan(device_host)


def webdav_upload(user, password, file_from, file_to, user_domain):
    return 'curl -T {2} http://{0}:{1}@{4}/remote.php/webdav/{3}'.format(user, password, file_from, file_to, user_domain)


def webdav_download(user, password, file_from, file_to, user_domain):
    return 'curl -o {3} http://{0}:{1}@{4}/remote.php/webdav/{2}'.format(user, password, file_from, file_to, user_domain)


def files_scan(device_host):
    run_ssh(device_host, '/opt/app/nextcloud/bin/occ-runner files:scan --all', password=DEVICE_PASSWORD)


def test_occ(device_host):
    run_ssh(device_host, '/opt/app/nextcloud/bin/occ-runner', password=DEVICE_PASSWORD)


def test_visible_through_platform(user_domain, device_host):
    response = requests.get('http://{0}/index.php/login'.format(device_host), headers={"Host": user_domain}, allow_redirects=False)
    assert response.status_code == 200, response.text


def test_admin(nextcloud_session_domain, user_domain, device_host):
    session, _ = nextcloud_session_domain
    response = session.get('http://{0}/index.php/settings/admin'.format(device_host), headers={"Host": user_domain}, allow_redirects=False)
    assert response.status_code == 200, response.text


def test_verification(nextcloud_session_domain, user_domain):
    session, _ = nextcloud_session_domain
    response = session.get('http://{0}/index.php/settings/integrity/failed'.format(user_domain), allow_redirects=False)
    print(response.text)
    assert response.status_code == 200, response.text
    assert 'INVALID_HASH' not in response.text
    assert 'EXCEPTION' not in response.text


# def test_integrity(nextcloud_session_domain, user_domain):
#     session, _ = nextcloud_session_domain
#     response = session.get('http://{0}/index.php/settings/ajax/checksetup'.format(user_domain), allow_redirects=False)
#     print(response.text)
#     assert response.status_code == 200, response.text
#     assert not json.loads(response.text)['hasPassedCodeIntegrityCheck'], 'you can fix me now'


def test_disk(syncloud_session, user_domain, device_host):

    loop_device_cleanup(device_host, '/tmp/test0', DEVICE_PASSWORD)
    loop_device_cleanup(device_host, '/tmp/test1', DEVICE_PASSWORD)

    device0 = loop_device_add(device_host, 'ext4', '/tmp/test0', DEVICE_PASSWORD)
    __activate_disk(syncloud_session, device0, device_host)
    __create_test_dir('test0', user_domain, device_host)
    __check_test_dir(nextcloud_session_domain(user_domain, device_host), 'test0', user_domain, device_host)

    device1 = loop_device_add(device_host, 'ext2', '/tmp/test1', DEVICE_PASSWORD)
    __activate_disk(syncloud_session, device1, device_host)
    __create_test_dir('test1', user_domain, device_host)
    __check_test_dir(nextcloud_session_domain(user_domain, device_host), 'test1', user_domain, device_host)

    __activate_disk(syncloud_session, device0, device_host)
    __check_test_dir(nextcloud_session_domain(user_domain, device_host), 'test0', user_domain, device_host)


def __log_data_dir(device_host):
    run_ssh(device_host, 'ls -la /data', password=DEVICE_PASSWORD)
    run_ssh(device_host, 'ls -la /data/', password=DEVICE_PASSWORD)
    run_ssh(device_host, 'ls -la /data/nextcloud', password=DEVICE_PASSWORD)


def __activate_disk(syncloud_session, loop_device, device_host):

    __log_data_dir(device_host)
    response = syncloud_session.get('http://{0}/rest/settings/disk_activate'.format(device_host),
                                    params={'device': loop_device}, allow_redirects=False)
    __log_data_dir(device_host)
    files_scan(device_host)
    assert response.status_code == 200, response.text


def __create_test_dir(test_dir, user_domain, device_host):
    response = requests.request('MKCOL', 'http://{0}:{1}@{2}/remote.php/webdav/{3}'.format(
        DEVICE_USER, DEVICE_PASSWORD, device_host, test_dir),
                                headers={"Host": user_domain})
    print(response.text)
    assert response.status_code == 201, response.text


def __check_test_dir(nextcloud_session, test_dir, user_domain, device_host):

    response = requests.get('http://{0}'.format(device_host), headers={"Host": user_domain})
    assert response.status_code == 200, BeautifulSoup(response.text, "html.parser").find('li', class_='error')

    nextcloud, _ = nextcloud_session
    response = nextcloud.get('http://{0}/index.php/apps/files/ajax/list.php?dir=/'.format(device_host),
                             headers={"Host": user_domain},
                             allow_redirects=False)
    info = json.loads(response.text)
    print(response.text)
    dirs = map(lambda v: v['name'], info['data']['files'])
    assert test_dir in dirs, response.text


def test_phpinfo(device_host):
    run_ssh(device_host, '/opt/app/nextcloud/bin/php-runner -i > /opt/data/nextcloud/log/phpinfo.log', password=DEVICE_PASSWORD)


def test_remove(syncloud_session, device_host):
    response = syncloud_session.get('http://{0}/rest/remove?app_id=nextcloud'.format(device_host), allow_redirects=False)
    assert response.status_code == 200, response.text


def test_reinstall(app_archive_path, device_host):
    __local_install(app_archive_path, device_host)


def __local_install(app_archive_path, device_host):
    run_scp('{0} root@{1}:/app.tar.gz'.format(app_archive_path, device_host), password=DEVICE_PASSWORD)
    run_ssh(device_host, '/opt/app/sam/bin/sam --debug install /app.tar.gz', password=DEVICE_PASSWORD)
    time.sleep(3)
