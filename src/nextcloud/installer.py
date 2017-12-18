from os import symlink, environ
from os.path import isdir, join, isfile
import shutil
import uuid
from subprocess import check_output

import logging
from syncloud_app import logger

from syncloud_platform.gaplib import fs, linux, gen
from syncloud_platform.application import api

from nextcloud.postgres import Database
from nextcloud.cron import OwncloudCron
from nextcloud.octools import OCConsole, OCConfig
from nextcloud.webface import Setup

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
CRON_USER = APP_NAME
APP_CONFIG_PATH = '{0}/config'.format(APP_NAME)
PSQL_PORT = 5436


def database_init(logger, app_install_dir, app_data_dir, user_name):
    database_path = join(app_data_dir, 'database')
    if not isdir(database_path):
        psql_initdb = join(app_install_dir, 'postgresql/bin/initdb')
        logger.info(check_output(['sudo', '-H', '-u', user_name, psql_initdb, database_path]))
        postgresql_conf_to = join(database_path, 'postgresql.conf')
        postgresql_conf_from = join(app_data_dir, 'config', 'postgresql.conf')
        shutil.copy(postgresql_conf_from, postgresql_conf_to)
    else:
        logger.info('Database path "{0}" already exists'.format(database_path))


class OwncloudInstaller:
    def __init__(self):
        if not logger.factory_instance:
            logger.init(logging.DEBUG, True)

        self.log = logger.get_logger('{0}_installer'.format(APP_NAME))
        self.app = api.get_app_setup(APP_NAME)
        self.database_path = join(self.app.get_data_dir(), 'database')
        self.occ = OCConsole(join(self.app.get_install_dir(), OCC_RUNNER_PATH))
        self.nextcloud_config_path = join(self.app.get_data_dir(), 'nextcloud', 'config')
        self.nextcloud_config_file = join(self.nextcloud_config_path, 'config.php')
        self.cron = OwncloudCron(self.app.get_install_dir(), self.app.get_data_dir(), APP_NAME, CRON_USER)

        environ['DATA_DIR'] = self.app.get_data_dir()

    def install(self):

        linux.fix_locale()

        linux.useradd(USER_NAME)

        templates_path = join(self.app.get_install_dir(), 'config.templates')
        app_data_dir = self.app.get_data_dir()
        config_path = join(app_data_dir, 'config')
        
        fs.makepath(self.nextcloud_config_path)
        
        # TODO: remove after 17.10
        old_nextcloud_config_file = join(config_path, 'config.php')
        if isfile(old_nextcloud_config_file) and not isfile(self.nextcloud_config_file):
            shutil.copy(old_nextcloud_config_file, self.nextcloud_config_file)
       
        variables = {
            'app_dir': self.app.get_install_dir(),
            'app_data_dir': app_data_dir,
            'db_psql_port': PSQL_PORT
        }
        gen.generate_files(templates_path, config_path, variables)

        default_config_file = join(config_path, 'config.php')
        if not isfile(self.nextcloud_config_file):
            shutil.copy(default_config_file, self.nextcloud_config_file)
        
        fs.chownpath(self.app.get_install_dir(), USER_NAME, recursive=True)

        log_dir = join(app_data_dir, 'log')

        fs.makepath(log_dir)
        
        fs.chownpath(app_data_dir, USER_NAME, recursive=True)

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

        self.cron.remove()
        self.cron.create()

        oc_config = OCConfig(join(self.app.get_install_dir(), OC_CONFIG_PATH))
        oc_config.set_value('memcache.local', '\OC\Memcache\APCu')
        oc_config.set_value('loglevel', '2')
        oc_config.set_value('logfile', join(self.app.get_data_dir(), OWNCLOUD_LOG_PATH))
        oc_config.set_value('datadirectory', self.app.get_storage_dir())

        self.on_domain_change()

        fs.chownpath(self.app.get_data_dir(), USER_NAME, recursive=True)

    def remove(self):

        self.app.remove_service(SYSTEMD_NGINX_NAME)
        self.app.remove_service(SYSTEMD_PHP_FPM_NAME)
        self.app.remove_service(SYSTEMD_POSTGRESQL)

        self.cron.remove()

        if isdir(self.app.get_install_dir()):
            shutil.rmtree(self.app.get_install_dir())

    def installed(self):
        return 'installed' in open(self.nextcloud_config_file).read().strip()

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

        web_setup = Setup(self.app.get_data_dir())
        web_setup.finish(INSTALL_USER, unicode(uuid.uuid4().hex), self.app.get_storage_dir(), self.database_path, PSQL_PORT)
        #self.occ.run('maintenance:install  --database psql --database-name nextcloud --database-user {0} --database-pass {1} --admin-user {2} --admin-pass {3}'.format(DB_USER, DB_PASSWORD, INSTALL_USER, unicode(uuid.uuid4().hex)))

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
        self.occ.run('ldap:set-config s01 ldapGroupFilterGroups syncloud')
        self.occ.run('ldap:set-config s01 ldapGroupMemberAssocAttr memberUid')

        self.occ.run('ldap:set-config s01 ldapTLS 0')
        self.occ.run('ldap:set-config s01 turnOffCertCheck 1')
        self.occ.run('ldap:set-config s01 ldapConfigurationActive 1')

        self.cron.run()

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
        ocdata = join(app_storage_dir, '.ocdata')
        fs.touchfile(ocdata)
        check_output('chown {0}. {1}'.format(USER_NAME, ocdata), shell=True)
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
