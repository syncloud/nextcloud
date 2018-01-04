from crontab import CronTab
from subprocess import check_output
from syncloud_app import logger
from os.path import join


class OwncloudCron:

    def __init__(self, app_dir, data_dir, app_name, cron_user):
        self.cron_cmd = 'DATA_DIR={0} {1}'.format(data_dir, join(app_dir, 'bin/{0}-cron'.format(app_name)))
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
        self.log.info(check_output('sudo -E -H -u {0} {1}'.format(self.cron_user, self.cron_cmd), shell=True))