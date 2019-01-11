from syncloud_app import logger
from subprocess import check_output


class Database:

    def __init__(self, database, user):
        self.database = database
        self.user = user

    def execute(self, sql):
        log = logger.get_logger('psql')
        log.info("executing: {0}".format(sql))
        log.info(check_output('snap run nextcloud.psql -U {0} -d {1} -c "{2}"'.format(
            self.user, self.database, sql,
        ), shell=True))
