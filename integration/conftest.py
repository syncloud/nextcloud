import pytest

SYNCLOUD_INFO = 'syncloud.info'
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'


def pytest_addoption(parser):
    parser.addoption("--email", action="store")
    parser.addoption("--password", action="store")
    parser.addoption("--domain", action="store")
    parser.addoption("--release", action="store")
    parser.addoption("--installer", action="store")
    parser.addoption("--device-host", action="store")
    parser.addoption("--app-archive-path", action="store")


@pytest.fixture(scope="session")
def auth(request):
    config = request.config
    return config.getoption("--email"), \
           config.getoption("--password"), \
           config.getoption("--domain"), \
           config.getoption("--release")


@pytest.fixture(scope='module')
def user_domain(request):
    return 'nextcloud.{0}.{1}'.format(request.config.getoption("--domain"), SYNCLOUD_INFO)


@pytest.fixture(scope='module')
def app_archive_path(request):
    return request.config.getoption("--app-archive-path")

@pytest.fixture(scope='session')
def installer(request):
    return request.config.getoption("--installer")

@pytest.fixture(scope='session')
def device_host(request):
    return request.config.getoption("--device-host")