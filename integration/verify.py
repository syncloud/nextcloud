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
from integration.util.ssh import run_scp, ssh_command, SSH, run_ssh, set_docker_ssh_port

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
def module_setup(request):
    request.addfinalizer(module_teardown)


def module_teardown():
    os.mkdir(LOG_DIR)
    platform_log_dir = join(LOG_DIR, 'platform_log')
    os.mkdir(platform_log_dir)
    run_scp('root@localhost:/opt/data/platform/log/* {0}'.format(platform_log_dir), password=LOGS_SSH_PASSWORD)
    owncloud_log_dir = join(LOG_DIR, 'owncloud_log')
    os.mkdir(owncloud_log_dir)
    run_scp('root@localhost:/opt/data/owncloud/log/*.log {0}'.format(owncloud_log_dir), password=LOGS_SSH_PASSWORD)

    print('-------------------------------------------------------')
    print('syncloud docker image is running')
    print('connect using: {0}'.format(ssh_command(DEVICE_PASSWORD, SSH)))
    print('-------------------------------------------------------')


@pytest.fixture(scope='function')
def syncloud_session():
    session = requests.session()
    session.post('http://localhost/rest/login', data={'name': DEVICE_USER, 'password': DEVICE_PASSWORD})
    return session


@pytest.fixture(scope='function')
def owncloud_session_domain(user_domain):
    session = requests.session()
    response = session.get('http://127.0.0.1', headers={"Host": user_domain}, allow_redirects=False)
    soup = BeautifulSoup(response.text, "html.parser")
    requesttoken = soup.find_all('input', {'name': 'requesttoken'})[0]['value']
    response = session.post('http://127.0.0.1/index.php',
                            headers={"Host": user_domain},
                            data={'user': DEVICE_USER, 'password': DEVICE_PASSWORD, 'requesttoken': requesttoken},
                            allow_redirects=False)
    assert response.status_code == 302, response.text
    return session, requesttoken


def test_start(module_setup):
    shutil.rmtree(LOG_DIR, ignore_errors=True)


def test_activate_device(auth):
    email, password, domain, release, version, arch = auth

    run_ssh('/opt/app/sam/bin/sam update --release {0}'.format(release), password=DEFAULT_DEVICE_PASSWORD)
    run_ssh('/opt/app/sam/bin/sam --debug upgrade platform', password=DEFAULT_DEVICE_PASSWORD)

    response = requests.post('http://localhost:81/rest/activate',
                             data={'main_domain': SYNCLOUD_INFO, 'redirect_email': email, 'redirect_password': password,
                                   'user_domain': domain, 'device_username': DEVICE_USER, 'device_password': DEVICE_PASSWORD})
    assert response.status_code == 200, response.text
    global LOGS_SSH_PASSWORD
    LOGS_SSH_PASSWORD = DEVICE_PASSWORD


# def test_enable_external_access(syncloud_session):
#     response = syncloud_session.get('http://localhost/server/rest/settings/set_protocol', params={'protocol': 'https'})
#     assert '"success": true' in response.text
#     assert response.status_code == 200


def test_install(auth):
    __local_install(auth)

def test_resource(owncloud_session_domain, user_domain):
    session, _ = owncloud_session_domain
    response = session.get('http://127.0.0.1/core/img/filetypes/text.png', headers={"Host": user_domain})
    assert response.status_code == 200, response.text


def test_sync_1m_file(user_domain):
    _test_sync(user_domain, 1)


def test_sync_300m_file(user_domain):
    _test_sync(user_domain, 300)


# def test_sync_3g_file(user_domain):
#     _test_sync(user_domain, 3000)


def sync_cmd(sync_dir, user_domain):
    return 'owncloudcmd -u {0} -p {1} {2} http://{3}'.format(DEVICE_USER, DEVICE_PASSWORD, sync_dir, user_domain)


def _test_sync(user_domain, megabites):

    sync_dir_upload = 'sync.test.upload'
    sync_file = 'test.file-{0}'.format(megabites)
    shutil.rmtree(sync_dir_upload, ignore_errors=True)
    os.mkdir(sync_dir_upload)
    sync_full_path_file = join(sync_dir_upload, sync_file)
    print(check_output('dd if=/dev/zero of={0} count={1} bs=1M'.format(sync_full_path_file, megabites), shell=True))
    print(check_output(sync_cmd(sync_dir_upload, user_domain), shell=True))

    sync_dir_download = 'sync.test.download'
    shutil.rmtree(sync_dir_download, ignore_errors=True)
    os.mkdir(sync_dir_download)
    print(check_output(sync_cmd(sync_dir_download, user_domain), shell=True))
    sync_full_path_file = join(sync_dir_download, sync_file)

    assert os.path.isfile(sync_full_path_file)
    run_ssh('rm /data/owncloud/{0}/files/{1}'.format(DEVICE_USER, sync_file), password=DEVICE_PASSWORD)
    files_scan()


def files_scan():
    run_ssh('/opt/app/owncloud/bin/occ-runner files:scan --all', password=DEVICE_PASSWORD)


def test_visible_through_platform(auth, user_domain):
    response = requests.get('http://127.0.0.1', headers={"Host": user_domain}, allow_redirects=False)
    assert response.status_code == 200, response.text


def test_admin(owncloud_session_domain, user_domain):
    session, _ = owncloud_session_domain
    response = session.get('http://127.0.0.1/index.php/settings/admin', headers={"Host": user_domain}, allow_redirects=False)
    assert response.status_code == 200, response.text


def test_verification(owncloud_session_domain, user_domain):
    session, _ = owncloud_session_domain
    response = session.get('http://{0}/index.php/settings/integrity/failed'.format(user_domain), allow_redirects=False)
    print(response.text)
    assert response.status_code == 200, response.text
    assert 'INVALID_HASH' not in response.text
    assert 'EXCEPTION' not in response.text


# def test_integrity(owncloud_session_domain, user_domain):
#     session, _ = owncloud_session_domain
#     response = session.get('http://{0}/index.php/settings/ajax/checksetup'.format(user_domain), allow_redirects=False)
#     print(response.text)
#     assert response.status_code == 200, response.text
#     assert not json.loads(response.text)['hasPassedCodeIntegrityCheck'], 'you can fix me now'


def test_disk(syncloud_session, user_domain):

    loop_device_cleanup(0, DEVICE_PASSWORD)
    loop_device_cleanup(1, DEVICE_PASSWORD)

    device0 = loop_device_add('ext4', 0, DEVICE_PASSWORD)
    __activate_disk(syncloud_session, device0)
    __create_test_dir('test0', user_domain)
    __check_test_dir(owncloud_session_domain(user_domain), 'test0', user_domain)

    device1 = loop_device_add('ext2', 1, DEVICE_PASSWORD)
    __activate_disk(syncloud_session, device1)
    __create_test_dir('test1', user_domain)
    __check_test_dir(owncloud_session_domain(user_domain), 'test1', user_domain)

    __activate_disk(syncloud_session, device0)
    __check_test_dir(owncloud_session_domain(user_domain), 'test0', user_domain)

    #loop_device_cleanup(0, DEVICE_PASSWORD)
    #loop_device_cleanup(1, DEVICE_PASSWORD)


def __activate_disk(syncloud_session, loop_device):
    response = syncloud_session.get('http://localhost/rest/settings/disk_activate',
                                    params={'device': loop_device}, allow_redirects=False)
    files_scan()
    assert response.status_code == 200, response.text


def __create_test_dir(test_dir, user_domain):
    response = requests.request('MKCOL', 'http://{0}:{1}@127.0.0.1/remote.php/webdav/{2}'.format(
        DEVICE_USER, DEVICE_PASSWORD, test_dir),
                                headers={"Host": user_domain})
    print(response.text)
    assert response.status_code == 201, response.text


def __check_test_dir(owncloud_session, test_dir, user_domain):

    response = requests.get('http://127.0.0.1', headers={"Host": user_domain})
    assert response.status_code == 200, BeautifulSoup(response.text, "html.parser").find('li', class_='error')

    owncloud, _ = owncloud_session
    response = owncloud.get('http://127.0.0.1/index.php/apps/files/ajax/list.php?dir=/',
                            headers={"Host": user_domain},
                            allow_redirects=False)
    info = json.loads(response.text)
    print(response.text)
    dirs = map(lambda v: v['name'], info['data']['files'])
    assert test_dir in dirs, response.text


def test_remove(syncloud_session):
    response = syncloud_session.get('http://localhost/rest/remove?app_id=owncloud', allow_redirects=False)
    assert response.status_code == 200, response.text


def test_reinstall(auth):
    __local_install(auth)


def __local_install(auth):
    email, password, domain, release, version, arch = auth
    run_scp('{0}/../owncloud-{1}-{2}.tar.gz root@localhost:/'.format(DIR, version, arch), password=DEVICE_PASSWORD)
    run_ssh('/opt/app/sam/bin/sam --debug install /owncloud-{0}-{1}.tar.gz'.format(version, arch), password=DEVICE_PASSWORD)
    set_docker_ssh_port(DEVICE_PASSWORD)
    time.sleep(3)
