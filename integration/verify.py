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
    nextcloud_log_dir = join(LOG_DIR, 'nextcloud_log')
    os.mkdir(nextcloud_log_dir)
    run_scp('root@localhost:/opt/data/nextcloud/log/*.log {0}'.format(nextcloud_log_dir), password=LOGS_SSH_PASSWORD)

    run_scp('root@localhost:/var/log/sam.log {0}'.format(platform_log_dir), password=LOGS_SSH_PASSWORD)

    print('systemd logs')
    run_ssh('journalctl | tail -200', password=LOGS_SSH_PASSWORD)

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
def nextcloud_session_domain(user_domain):
    session = requests.session()
    response = session.get('http://127.0.0.1/index.php/login', headers={"Host": user_domain}, allow_redirects=False)
    soup = BeautifulSoup(response.text, "html.parser")
    requesttoken = soup.find_all('input', {'name': 'requesttoken'})[0]['value']
    response = session.post('http://127.0.0.1/index.php/login',
                            headers={"Host": user_domain},
                            data={'user': DEVICE_USER, 'password': DEVICE_PASSWORD, 'requesttoken': requesttoken},
                            allow_redirects=False)
    assert response.status_code == 303, response.text
    return session, requesttoken


def test_start(module_setup):
    shutil.rmtree(LOG_DIR, ignore_errors=True)


def test_activate_device(auth):
    email, password, domain, release, _ = auth

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


def test_install(app_archive_path):
    __local_install(app_archive_path)


def test_resource(nextcloud_session_domain, user_domain):
    session, _ = nextcloud_session_domain
    response = session.get('http://127.0.0.1/core/img/loading.gif', headers={"Host": user_domain})
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("megabytes", [1, 300, 3000])
def test_sync(user_domain, megabytes):

    sync_file = 'test.file-{0}'.format(megabytes)
    if os.path.isfile(sync_file):
        os.remove(sync_file)
    print(check_output('dd if=/dev/zero of={0} count={1} bs=1M'.format(sync_file, megabytes), shell=True))
    print(check_output(webdav_upload(DEVICE_USER, DEVICE_PASSWORD, sync_file, user_domain), shell=True))

    sync_file_download = 'test.file.download'
    if os.path.isfile(sync_file_download):
        os.remove(sync_file_download)
    print(check_output(webdav_download(DEVICE_USER, DEVICE_PASSWORD, sync_file_download, user_domain), shell=True))

    assert os.path.isfile(sync_file_download)
    run_ssh('rm /data/nextcloud/{0}/files/{1}'.format(DEVICE_USER, sync_file), password=DEVICE_PASSWORD)
    files_scan()


def webdav_upload(user, password, sync_file, user_domain):
    return 'curl -T {2} http://{0}:{1}@{3}/remote.php/webdav/{2}'.format(user, password, sync_file, user_domain)


def webdav_download(user, password, sync_file, user_domain):
    return 'curl -O {2} http://{0}:{1}@{3}/remote.php/webdav/{2}'.format(user, password, sync_file, user_domain)


def files_scan():
    run_ssh('/opt/app/nextcloud/bin/occ-runner files:scan --all', password=DEVICE_PASSWORD)


def test_visible_through_platform(user_domain):
    response = requests.get('http://127.0.0.1/index.php/login', headers={"Host": user_domain}, allow_redirects=False)
    assert response.status_code == 200, response.text


def test_admin(nextcloud_session_domain, user_domain):
    session, _ = nextcloud_session_domain
    response = session.get('http://127.0.0.1/index.php/settings/admin', headers={"Host": user_domain}, allow_redirects=False)
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


def test_disk(syncloud_session, user_domain):

    loop_device_cleanup('/tmp/test0', DEVICE_PASSWORD)
    loop_device_cleanup('/tmp/test1', DEVICE_PASSWORD)

    device0 = loop_device_add('ext4', '/tmp/test0', DEVICE_PASSWORD)
    __activate_disk(syncloud_session, device0)
    __create_test_dir('test0', user_domain)
    __check_test_dir(nextcloud_session_domain(user_domain), 'test0', user_domain)

    device1 = loop_device_add('ext2', '/tmp/test1', DEVICE_PASSWORD)
    __activate_disk(syncloud_session, device1)
    __create_test_dir('test1', user_domain)
    __check_test_dir(nextcloud_session_domain(user_domain), 'test1', user_domain)

    __activate_disk(syncloud_session, device0)
    __check_test_dir(nextcloud_session_domain(user_domain), 'test0', user_domain)


def __log_data_dir():
    run_ssh('ls -la /data', password=DEVICE_PASSWORD)
    run_ssh('ls -la /data/', password=DEVICE_PASSWORD)
    run_ssh('ls -la /data/nextcloud', password=DEVICE_PASSWORD)


def __activate_disk(syncloud_session, loop_device):

    __log_data_dir()
    response = syncloud_session.get('http://localhost/rest/settings/disk_activate',
                                    params={'device': loop_device}, allow_redirects=False)
    __log_data_dir()
    files_scan()
    assert response.status_code == 200, response.text


def __create_test_dir(test_dir, user_domain):
    response = requests.request('MKCOL', 'http://{0}:{1}@127.0.0.1/remote.php/webdav/{2}'.format(
        DEVICE_USER, DEVICE_PASSWORD, test_dir),
                                headers={"Host": user_domain})
    print(response.text)
    assert response.status_code == 201, response.text


def __check_test_dir(nextcloud_session, test_dir, user_domain):

    response = requests.get('http://127.0.0.1', headers={"Host": user_domain})
    assert response.status_code == 200, BeautifulSoup(response.text, "html.parser").find('li', class_='error')

    nextcloud, _ = nextcloud_session
    response = nextcloud.get('http://127.0.0.1/index.php/apps/files/ajax/list.php?dir=/',
                             headers={"Host": user_domain},
                             allow_redirects=False)
    info = json.loads(response.text)
    print(response.text)
    dirs = map(lambda v: v['name'], info['data']['files'])
    assert test_dir in dirs, response.text


def test_remove(syncloud_session):
    response = syncloud_session.get('http://localhost/rest/remove?app_id=nextcloud', allow_redirects=False)
    assert response.status_code == 200, response.text


def test_reinstall(app_archive_path):
    __local_install(app_archive_path)


def __local_install(app_archive_path):
    run_scp('{0} root@localhost:/app.tar.gz'.format(app_archive_path), password=DEVICE_PASSWORD)
    run_ssh('/opt/app/sam/bin/sam --debug install /app.tar.gz', password=DEVICE_PASSWORD)
    set_docker_ssh_port(DEVICE_PASSWORD)
    time.sleep(3)
