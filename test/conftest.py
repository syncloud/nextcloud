from os.path import dirname, join
from syncloudlib.integration.conftest import *
from syncloudlib.integration.selenium_conftest import *

DIR = dirname(__file__)


@pytest.fixture(scope="session")
def project_dir():
    return join(DIR, '..')
