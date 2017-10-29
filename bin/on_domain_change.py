from os.path import dirname, join, abspath, isdir
from os import listdir
import sys

app_path = abspath(join(dirname(__file__), '..', '..', 'nextcloud'))
sys.path.append(join(app_path, 'src'))

lib_path = join(app_path, 'lib')
libs = [join(lib_path, item) for item in listdir(lib_path) if isdir(join(lib_path, item))]
map(sys.path.append, libs)

from nextcloud.installer import OwncloudInstaller
OwncloudInstaller().on_domain_change()
