from subprocess import check_output, CalledProcessError
from syncloudlib import logger


class OCConsole:
    def __init__(self, occ_runner_path):
        self.occ_runner_path = occ_runner_path
        self.log = logger.get_logger('nextcloud_occ')

    def run(self, args):

        try:
            output = check_output('{0} {1}'.format(self.occ_runner_path, args), shell=True).decode().strip()
            if output:
                self.log.info(output)
            return output
        except CalledProcessError as e:
            self.log.error("occ error: " + e.output.decode())
            raise e


class OCConfig:
    def __init__(self, oc_config_path):
        self.oc_config_path = oc_config_path
        self.log = logger.get_logger('nextcloud_config')
        
    def set_value(self, key, value):
        self.log.info('setting value: {0} = {1}'.format(key, value))
        try:
            output = check_output('{0} {1} {2}'.format(
                self.oc_config_path,
                key,
                value), shell=True).decode().strip()
            if output:
                self.log.info(output)
        except CalledProcessError as e:
            self.log.error("occ config error: " + e.output.decode())
            raise e
