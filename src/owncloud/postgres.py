from syncloud_app import logger
from subprocess import check_output


class Database:

    def __init__(self, psql, database, user, database_path, port):
        self.psql = psql
        self.database = database
        self.user = user
        self.database_path = database_path
        self.port = port

    def execute(self, sql):
        log = logger.get_logger('nextcloud_postgres')
        log.info("executing: {0}".format(sql))
        log.info(check_output('{0} -U {1} -d {2} -c "{3}" -h {4} -p {5}'.format(
            self.psql, self.user, self.database, sql, self.database_path, self.port,
        ), shell=True))
