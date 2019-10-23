import shutil
from os.path import join
from subprocess import check_output

from syncloudlib import logger


class Database:

    def __init__(self):
        pass

    def init(self, app_dir, app_data_dir):
        log = logger.get_logger('initdb')
        database_path = join(app_data_dir, 'database')
        cmd = join(app_dir, 'bin/initdb.sh')
        log.info(check_output([cmd, database_path]))
        postgresql_conf_from = join(app_data_dir, 'config', 'postgresql.conf')
        postgresql_conf_to = join(database_path, 'postgresql.conf')
        shutil.copy(postgresql_conf_from, postgresql_conf_to)

    def execute(self, database, user, sql):
        log = logger.get_logger('psql')
        log.info("executing: {0}".format(sql))
        cmd = 'snap run nextcloud.psql -U {0} -d {1} -c "{2}"'.format(user, database, sql)
        log.info(check_output(cmd, shell=True))

    def dumpall(self, file):
        log = logger.get_logger('pg_dumpall')
        cmd = 'snap run nextcloud.pgdumpall -f {0}'.format(file)
        log.info("executing: {0}".format(cmd))
        log.info(check_output(cmd, shell=True))
