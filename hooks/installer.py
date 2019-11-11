import logging
import os
import shutil
import uuid
from os.path import isfile
from os.path import join
from os.path import realpath
from subprocess import check_output, CalledProcessError

from crontab import CronTab
from syncloudlib import fs, linux, gen, logger
from syncloudlib.application import paths, urls, storage, service

from octools import OCConsole, OCConfig
from postgres import Database

APP_NAME = 'nextcloud'

INSTALL_USER = 'installer'
USER_NAME = APP_NAME
DB_NAME = APP_NAME
DB_USER = APP_NAME
DB_PASSWORD = APP_NAME
OCC_RUNNER_PATH = 'bin/occ-runner'
LOG_PATH = 'log/{0}.log'.format(APP_NAME)
CRON_USER = APP_NAME
APP_CONFIG_PATH = '{0}/config'.format(APP_NAME)
PSQL_PORT = 5436

SYSTEMD_NGINX = '{0}.nginx'.format(APP_NAME)
SYSTEMD_PHP_FPM = '{0}.php-fpm'.format(APP_NAME)
SYSTEMD_POSTGRESQL = '{0}.postgresql'.format(APP_NAME)


class Installer:
    def __init__(self):
        if not logger.factory_instance:
            logger.init(logging.DEBUG, True)

        self.log = logger.get_logger('nextcloud_installer')
        self.app_dir = paths.get_app_dir(APP_NAME)
        self.common_dir = paths.get_data_dir(APP_NAME)
        self.data_dir = join('/var/snap', APP_NAME, 'current')
        self.config_dir = join(self.data_dir, 'config')
        self.extra_apps_dir = join(self.data_dir, 'extra-apps')
        self.occ = OCConsole(join(self.app_dir, OCC_RUNNER_PATH))
        self.nextcloud_config_path = join(self.data_dir, 'nextcloud', 'config')
        self.nextcloud_config_file = join(self.nextcloud_config_path, 'config.php')
        self.cron = Cron(CRON_USER)
        self.db = Database(self.app_dir, self.data_dir, self.config_dir, PSQL_PORT)
        self.oc_config = OCConfig(join(self.app_dir, 'bin/nextcloud-config'))

    def install_config(self):

        home_folder = join('/home', USER_NAME)
        linux.useradd(USER_NAME, home_folder=home_folder)
        storage.init_storage(APP_NAME, USER_NAME)
        templates_path = join(self.app_dir, 'config.templates')

        variables = {
            'app_dir': self.app_dir,
            'common_dir': self.common_dir,
            'data_dir': self.data_dir,
            'db_psql_port': PSQL_PORT,
            'database_dir': self.db.database_dir,
            'config_dir': self.config_dir,
        }
        gen.generate_files(templates_path, self.config_dir, variables)

        fs.makepath(self.nextcloud_config_path)
        fs.makepath(join(self.common_dir, 'log'))
        fs.makepath(join(self.common_dir, 'nginx'))
        fs.makepath(self.extra_apps_dir)

        fs.chownpath(self.common_dir, USER_NAME, recursive=True)
        fs.chownpath(self.data_dir, USER_NAME, recursive=True)

    def install(self):
        self.install_config()

        default_config_file = join(self.config_dir, 'config.php')
        shutil.copy(default_config_file, self.nextcloud_config_file)
        fs.chownpath(self.nextcloud_config_path, USER_NAME, recursive=True)

        self.db.init()

    def pre_refresh(self):
        self.db.backup()

    def post_refresh(self):
        self.install_config()
        self.migrate_nextcloud_config_file()

        if self.db.requires_upgrade():
            self.db.remove()
            self.db.init()

    def configure(self):
        self.prepare_storage()
        app_storage_dir = storage.init_storage(APP_NAME, USER_NAME)

        if self.installed():
            self.upgrade()
        else:
            self.initialize(app_storage_dir)
        
        self.occ.run('ldap:set-config s01 ldapEmailAttribute mail')
        self.occ.run('config:system:set apps_paths 1 path --value="{0}"'.format(self.extra_apps_dir))
        self.occ.run('config:system:set dbhost --value="{0}"'.format(self.db.database_host))
        # migrate to systemd cron units
        self.cron.remove()
        self.cron.create()

        self.oc_config.set_value('memcache.local', "'\\OC\\Memcache\\APCu'")
        self.oc_config.set_value('loglevel', '2')
        self.oc_config.set_value('logfile', join(self.common_dir, LOG_PATH))
        real_app_storage_dir = realpath(app_storage_dir)
        self.oc_config.set_value('datadirectory', real_app_storage_dir)
        # oc_config.set_value('integrity.check.disabled', 'true')
        self.oc_config.set_value('mail_smtpmode', 'smtp')
        self.oc_config.set_value('mail_smtphost', 'localhost:25')
        # oc_config.set_value('mail_smtpsecure', '')
        self.oc_config.set_value('mail_smtpauth', 'false')
        # oc_config.set_value('mail_smtpname', '')
        # oc_config.set_value('mail_smtppassword', '')
        
        self.on_domain_change()

        fs.chownpath(self.common_dir, USER_NAME, recursive=True)
        fs.chownpath(self.data_dir, USER_NAME, recursive=True)

    def migrate_nextcloud_config_file(self):
        # Migrate from common dir to data dir
        if not isfile(self.nextcloud_config_file):
            old_nextcloud_config_file = join(self.common_dir, 'nextcloud', 'config', 'config.php')
            if isfile(old_nextcloud_config_file):
                old_database_dir = join(self.common_dir, 'database')
                with open(old_nextcloud_config_file) as f:
                    content = f.read().replace(old_database_dir, self.db.get_database_path())
                with open(self.nextcloud_config_file, "w") as f:
                    f.write(content)
                fs.chownpath(self.nextcloud_config_path, USER_NAME, recursive=True)


    def installed(self):
        return 'installed' in open(self.nextcloud_config_file).read().strip()

    def upgrade(self):
        if self.db.requires_upgrade():
            self.db.restore()

        if 'require upgrade' in self.occ.run('status'):
            self.occ.run('maintenance:mode --on')

            try:
                self.occ.run('upgrade')
            except CalledProcessError, e:
                self.log.warn('unable to upgrade')
                self.log.warn(e.output)

            self.occ.run('maintenance:mode --off')
            self.occ.run('db:add-missing-indices')

    def initialize(self, app_storage_dir):

        self.db.execute('postgres', DB_USER, "ALTER USER {0} WITH PASSWORD '{1}';".format(DB_USER, DB_PASSWORD))
        real_app_storage_dir = realpath(app_storage_dir)
        self.occ.run('maintenance:install  --database pgsql --database-host {0}:{1}'
                     ' --database-name nextcloud --database-user {2} --database-pass {3}'
                     ' --admin-user {4} --admin-pass {5} --data-dir {6}'
                     .format(self.db.get_database_path(), PSQL_PORT, DB_USER, DB_PASSWORD,
                             INSTALL_USER, unicode(uuid.uuid4().hex), real_app_storage_dir))

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

        self.occ.run('ldap:set-config s01 hasMemberOfFilterSupport 0')
        self.occ.run('ldap:set-config s01 ldapLoginFilter "(&(|(objectclass=inetOrgPerson))(uid=%uid))"')

        self.occ.run('ldap:set-config s01 ldapUserFilter "(|(objectclass=inetOrgPerson))"')
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
        
        self.occ.run('db:convert-filecache-bigint')

        self.cron.run()

        self.db.execute(DB_NAME, DB_USER, "update oc_ldap_group_mapping set owncloud_name = 'admin';")
        self.db.execute(DB_NAME, DB_USER, "update oc_ldap_group_members set owncloudname = 'admin';")

        self.occ.run('user:delete {0}'.format(INSTALL_USER))
        self.occ.run('db:add-missing-indices')

    def on_disk_change(self):
        
        self.prepare_storage()
        self.occ.run('config:system:delete instanceid')
        service.restart(SYSTEMD_PHP_FPM)
        service.restart(SYSTEMD_NGINX)

    def prepare_storage(self):
        app_storage_dir = storage.init_storage(APP_NAME, USER_NAME)
        ocdata = join(app_storage_dir, '.ocdata')
        fs.touchfile(ocdata)
        check_output('chown {0}. {1}'.format(USER_NAME, ocdata), shell=True)
        check_output('chmod 770 {0}'.format(app_storage_dir), shell=True)
        tmp_storage_path = join(app_storage_dir, 'tmp')
        fs.makepath(tmp_storage_path)
        fs.chownpath(tmp_storage_path, USER_NAME)
        real_app_storage_dir = realpath(app_storage_dir)
        self.oc_config.set_value('datadirectory', real_app_storage_dir)

    def on_domain_change(self):
        app_domain = urls.get_app_domain_name(APP_NAME)
        local_ip = check_output(["hostname", "-I"]).split(" ")[0]
        self.oc_config.set_value('trusted_domains', "localhost {0} {1}".format(local_ip, app_domain))


class Cron:

    def __init__(self, cron_user):
        self.cron_cmd = '/usr/bin/snap run nextcloud.cron'
        self.cron_user = cron_user
        self.log = logger.get_logger('cron')

    def remove(self):
        print("remove crontab task")
        cron = CronTab(user=self.cron_user)
        for job in cron.find_command(self.cron_user):
            cron.remove(job)
        cron.write()

    def create(self):
        cron = CronTab(user=self.cron_user)
        print("create crontab task")
        ci_job = cron.new(command=self.cron_cmd)
        ci_job.setall('*/15 * * * *')
        cron.write()

    def run(self):
        self.log.info("running: {0}".format(self.cron_cmd))
        self.log.info(check_output(self.cron_cmd, shell=True))
