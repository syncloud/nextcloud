from os import symlink
from os.path import isdir, join, isfile
import shutil
import uuid
from subprocess import check_output

from syncloud_app import logger

from syncloud_platform.gaplib import fs, linux, gen
from syncloud_platform.application import api

from owncloud.postgres import Database
from owncloud.cron import OwncloudCron
from owncloud.octools import OCConsole, OCConfig
from owncloud.webface import Setup

APP_NAME = 'nextcloud'

SYSTEMD_NGINX_NAME = '{0}-nginx'.format(APP_NAME)
SYSTEMD_PHP_FPM_NAME = '{0}-php-fpm'.format(APP_NAME)
SYSTEMD_POSTGRESQL = '{0}-postgresql'.format(APP_NAME)
INSTALL_USER = 'installer'
USER_NAME = APP_NAME
DB_NAME = APP_NAME
DB_USER = APP_NAME
DB_PASSWORD = APP_NAME
PSQL_PATH = 'postgresql/bin/psql'
OCC_RUNNER_PATH = 'bin/occ-runner'
OC_CONFIG_PATH = 'bin/{0}-config'.format(APP_NAME)
OWNCLOUD_LOG_PATH = 'log/{0}.log'.format(APP_NAME)
CRON_CMD = 'bin/{0}-cron'.format(APP_NAME)
CRON_USER = APP_NAME
APP_CONFIG_PATH = '{0}/config'.format(APP_NAME)
DATA_CONFIG_FILE_PATH = 'config/config.php'
PSQL_PORT = 5436
WEB_PORT = 1085


def database_init(logger, app_install_dir, app_data_dir, user_name):
    database_path = join(app_data_dir, 'database')
    if not isdir(database_path):
        psql_initdb = join(app_install_dir, 'postgresql/bin/initdb')
        logger.info(check_output(['sudo', '-H', '-u', user_name, psql_initdb, database_path]))
        postgresql_conf_to = join(database_path, 'postgresql.conf')
        postgresql_conf_from = join(app_install_dir, 'config', 'postgresql.conf')
        shutil.copy(postgresql_conf_from, postgresql_conf_to)
    else:
        logger.info('Database path "{0}" already exists'.format(database_path))


class OwncloudInstaller:
    def __init__(self):
        self.log = logger.get_logger('{0}_installer'.format(APP_NAME))
        self.app = api.get_app_setup(APP_NAME)
        self.database_path = join(self.app.get_data_dir(), 'database')
        self.occ = OCConsole(join(self.app.get_install_dir(), OCC_RUNNER_PATH))

    def install(self):

        linux.fix_locale()

        linux.useradd(USER_NAME)

        templates_path = join(self.app.get_install_dir(), 'config.templates')
        config_path = join(self.app.get_install_dir(), 'config')

        app_data_dir = self.app.get_data_dir()

        variables = {
            'app_dir': self.app.get_install_dir(),
            'app_data_dir': app_data_dir,
            'web_port': WEB_PORT,
            'db_psql_port': PSQL_PORT
        }
        gen.generate_files(templates_path, config_path, variables)
        fs.chownpath(self.app.get_install_dir(), USER_NAME, recursive=True)

        config_data_dir = join(app_data_dir, 'config')
        log_dir = join(app_data_dir, 'log')

        fs.makepath(config_data_dir)
        fs.makepath(log_dir)

        fs.chownpath(app_data_dir, USER_NAME, recursive=True)

        config_app_dir = join(self.app.get_install_dir(), APP_CONFIG_PATH)
        symlink(config_data_dir, config_app_dir)

        database_init(self.log, self.app.get_install_dir(), self.app.get_data_dir(), USER_NAME)

        print("setup systemd")
        self.app.add_service(SYSTEMD_POSTGRESQL)
        self.app.add_service(SYSTEMD_PHP_FPM_NAME)
        self.app.add_service(SYSTEMD_NGINX_NAME)

        self.prepare_storage()

        if self.installed():
            self.upgrade()
        else:
            self.initialize()

        cron = OwncloudCron(join(self.app.get_install_dir(), CRON_CMD), CRON_USER)
        cron.remove()
        cron.create()

        oc_config = OCConfig(join(self.app.get_install_dir(), OC_CONFIG_PATH))
        oc_config.set_value('memcache.local', '\OC\Memcache\APCu')
        oc_config.set_value('loglevel', '2')
        oc_config.set_value('logfile', join(self.app.get_data_dir(), OWNCLOUD_LOG_PATH))
        oc_config.set_value('datadirectory', self.app.get_storage_dir())

        self.on_domain_change()

        fs.chownpath(self.app.get_data_dir(), USER_NAME, recursive=True)

        self.app.register_web(WEB_PORT)

    def remove(self):

        self.app.unregister_web()
        cron = OwncloudCron(join(self.app.get_install_dir(), CRON_CMD), CRON_USER)
        self.app.remove_service(SYSTEMD_NGINX_NAME)
        self.app.remove_service(SYSTEMD_PHP_FPM_NAME)
        self.app.remove_service(SYSTEMD_POSTGRESQL)

        cron.remove()

        if isdir(self.app.get_install_dir()):
            shutil.rmtree(self.app.get_install_dir())

    def installed(self):

        config_file = join(self.app.get_data_dir(), DATA_CONFIG_FILE_PATH)
        if not isfile(config_file):
            return False

        return 'installed' in open(config_file).read().strip()

    def upgrade(self):

        if 'require upgrade' in self.occ.run('status'):
            self.occ.run('maintenance:mode --on')
            self.occ.run('upgrade')
            self.occ.run('maintenance:mode --off')

    def initialize(self):

        print("initialization")

        print("creating database files")

        db_postgres = Database(
            join(self.app.get_install_dir(), PSQL_PATH),
            database='postgres', user=DB_USER, database_path=self.database_path, port=PSQL_PORT)
        db_postgres.execute("ALTER USER {0} WITH PASSWORD '{1}';".format(DB_USER, DB_PASSWORD))

        web_setup = Setup(WEB_PORT)
        web_setup.finish(INSTALL_USER, unicode(uuid.uuid4().hex), self.app.get_storage_dir(), self.database_path)

        self.occ.run('app:enable user_ldap')

        # https://doc.owncloud.org/server/8.0/admin_manual/configuration_server/occ_command.html
        # This is a holdover from the early days, when there was no option to create additional configurations.
        # The second, and all subsequent, configurations that you create are automatically assigned IDs:
        self.occ.run('ldap:create-empty-config')
        self.occ.run('ldap:create-empty-config')

        self.occ.run('ldap:set-config s01 ldapHost ldap://localhost')
        self.occ.run('ldap:set-config s01 ldapPort 389')
        self.occ.run('ldap:set-config s01 ldapAgentName dc=syncloud,dc=org')
        self.occ.run('ldap:set-config s01 ldapBase dc=syncloud,dc=org')
        self.occ.run('ldap:set-config s01 ldapAgentPassword syncloud')

        self.occ.run('ldap:set-config s01 ldapLoginFilter "(&(|(objectclass=inetOrgPerson))(uid=%uid))"')

        self.occ.run('ldap:set-config s01 ldapUserFilterObjectclass inetOrgPerson')
        self.occ.run('ldap:set-config s01 ldapBaseUsers ou=users,dc=syncloud,dc=org')
        self.occ.run('ldap:set-config s01 ldapUserDisplayName cn')
        self.occ.run('ldap:set-config s01 ldapExpertUsernameAttr cn')

        self.occ.run('ldap:set-config s01 ldapGroupFilterObjectclass posixGroup')
        self.occ.run('ldap:set-config s01 ldapGroupDisplayName cn')
        self.occ.run('ldap:set-config s01 ldapBaseGroups ou=groups,dc=syncloud,dc=org')
        self.occ.run('ldap:set-config s01 ldapGroupFilter "(&(|(objectclass=posixGroup)))"')
        self.occ.run('ldap:set-config s01 ldapGroupMemberAssocAttr memberUid')

        self.occ.run('ldap:set-config s01 ldapTLS 0')
        self.occ.run('ldap:set-config s01 turnOffCertCheck 1')
        self.occ.run('ldap:set-config s01 ldapConfigurationActive 1')

        cron = OwncloudCron(join(self.app.get_install_dir(), CRON_CMD), CRON_USER)
        cron.run()

        db = Database(join(self.app.get_install_dir(), PSQL_PATH),
                      database=DB_NAME, user=DB_USER, database_path=self.database_path, port=PSQL_PORT)
        db.execute("update oc_ldap_group_mapping set owncloud_name = 'admin';")
        db.execute("update oc_ldap_group_members set owncloudname = 'admin';")

        self.occ.run('user:delete {0}'.format(INSTALL_USER))

    def on_disk_change(self):
        self.prepare_storage()
        self.occ.run('config:system:delete instanceid')
        self.app.restart_service(SYSTEMD_PHP_FPM_NAME)
        self.app.restart_service(SYSTEMD_NGINX_NAME)

    def prepare_storage(self):
        app_storage_dir = self.app.init_storage(USER_NAME)
        fs.touchfile(join(app_storage_dir, '.ocdata'))
        check_output('chmod 770 {0}'.format(app_storage_dir), shell=True)
        tmp_storage_path = join(app_storage_dir, 'tmp')
        fs.makepath(tmp_storage_path)
        fs.chownpath(tmp_storage_path, USER_NAME)

    def on_domain_change(self):
        app_domain = self.app.app_domain_name()
        local_ip = check_output(["hostname", "-I"]).split(" ")[0]
        domains = ['localhost', local_ip, app_domain]
        oc_config = OCConfig(join(self.app.get_install_dir(), OC_CONFIG_PATH))
        oc_config.set_value('trusted_domains', " ".join(domains))
