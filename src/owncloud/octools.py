from subprocess import check_output
from syncloud_app import logger

class OCConsole:
    def __init__(self, occ_runner_path):
        self.occ_runner_path = occ_runner_path

    def run(self, args):
        log = logger.get_logger('owncloud.occ')
        output = check_output('{0} {1}'.format(self.occ_runner_path, args), shell=True).strip()
        if output:
            log.info(output)


class OCConfig:
    def __init__(self, oc_config_path):
        self.oc_config_path = oc_config_path

    def set_value(self, key, value):
        print(check_output('{0} {1} {2}'.format(
            self.oc_config_path,
            key,
            "'{0}'".format(value)), shell=True).strip())
