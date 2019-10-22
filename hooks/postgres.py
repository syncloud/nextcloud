from syncloudlib import logger
from subprocess import check_output


class Database:

    def __init__(self, database, user):
        self.database = database
        self.user = user

    def execute(self, sql):
        log = logger.get_logger('psql')
        log.info("executing: {0}".format(sql))
        cmd = 'snap run nextcloud.psql -U {0} -d {1} -c "{2}"'.format(self.user, self.database, sql)
        log.info(check_output(cmd, shell=True))

    def dumpall(self, file):
        log = logger.get_logger('pg_dumpall')
        cmd = 'snap run nextcloud.pgdumpall -f {0}'.format(self.user, self.database, file)
        log.info("executing: {0}".format(cmd))
        log.info(check_output(cmd, shell=True))
