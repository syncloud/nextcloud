import shutil
from os.path import join, isfile, isdir
from subprocess import check_output

from syncloudlib import logger


class Database:

    def __init__(self, app_dir, data_dir, config_path):
        self.log = logger.get_logger('database')
        self.app_dir = app_dir
        self.config_path = config_path
        self.data_dir = data_dir
        self.postgresql_config = join(self.config_path, 'postgresql.conf')
        self.database_path = join(self.data_dir, 'database')
        self.old_major_version_file = join(self.data_dir, 'db.major.version')
        self.new_major_version_file = join(self.app_dir, 'db.major.version')
        self.backup_file = join(self.data_dir, 'database.dump')

    def requires_upgrade(self):
        if not isfile(self.old_major_version_file):
            return True
        old_version = open(self.old_major_version_file).read().strip()
        new_version = open(self.new_major_version_file).read().strip()
        return old_version != new_version

    def get_database_path(self):
        return self.database_path

    def upgrade(self):
        if not isfile(self.backup_file):
            raise Exception("Backup file does not exist: {0}".format(self.backup_file))
        self.remove()
        self.init()
        self.restore()

    def remove(self):
        if isdir(self.database_path):
            shutil.rmtree(self.database_path)

    def init(self):
        cmd = join(self.app_dir, 'bin/initdb.sh')
        self.log.info(check_output([cmd, self.database_path]))
        shutil.copy(self.postgresql_config, self.database_path)

    def execute(self, database, user, sql):
        self.log.info("executing: {0}".format(sql))
        cmd = 'snap run nextcloud.psql -U {0} -d {1} -c "{2}"'.format(user, database, sql)
        self.log.info(check_output(cmd, shell=True))

    def restore(self):
        cmd = 'snap run nextcloud.psql -f {0} postgres'.format(self.backup_file)
        self.log.info("executing: {0}".format(cmd))
        self.log.info(check_output(cmd, shell=True))

    def backup(self):
        cmd = 'snap run nextcloud.pgdumpall -f {0}'.format(self.backup_file)
        self.log.info("executing: {0}".format(cmd))
        self.log.info(check_output(cmd, shell=True))
        shutil.copy(self.new_major_version_file, self.old_major_version_file)
