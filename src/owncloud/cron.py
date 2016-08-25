from crontab import CronTab
from subprocess import check_output
from syncloud_app import logger


class OwncloudCron:

    def __init__(self, cron_cmd, cron_user):
        self.cron_cmd = cron_cmd
        self.cron_user = cron_user
        self.cron = CronTab(user=self.cron_user)
        self.log = logger.get_logger('owncloud.cron')

    def remove(self):
        print("remove crontab task")

        for job in self.cron.find_command(self.cron_user):
            self.cron.remove(job)
        self.cron.write()

    def create(self):
        print("create crontab task")
        ci_job = self.cron.new(command=self.cron_cmd)
        ci_job.setall('*/15 * * * *')
        self.cron.write()

    def run(self):
        self.log.info("running: {0}".format(self.cron_cmd))
        self.log.info(check_output('sudo -H -u {0} {1}'.format(self.cron_user, self.cron_cmd), shell=True))