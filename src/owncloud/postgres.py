from syncloud_app import logger
from subprocess import check_output


class Database:

    def __init__(self, psql, database, user):
        self.psql = psql
        self.database = database
        self.user = user

    def execute(self, sql):
        log = logger.get_logger('owncloud_postgres')
        log.info("executing: {0}".format(sql))
        log.info(check_output('{0} -U {1} -d {2} -c "{3}"'.format(self.psql, self.user, self.database, sql), shell=True))
