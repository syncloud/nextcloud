import re


def convert_trusted_configuration(config, domain_port):
    prog = re.compile(r"'trusted_domains(?:\n|\r\n?|.)*array.*\((?:\n|\r\n?|.)*.*\),", re.MULTILINE)
    m = prog.search(config)
    trusted_conf = m.group(0)
    old_config = config.split(trusted_conf)
    return old_config[0] + "'trusted_domains' => array('{}'),".format(domain_port) + old_config[1]


def overwrite_webroot(config):

    prog = re.compile(r"'overwritewebroot'.*=>.*'.*'", re.MULTILINE)
    found = prog.search(config)
    if found:
        existing = found.group(0)
        old_config = config.split(existing)
        return old_config[0] + "'overwritewebroot' => '/owncloud'" + old_config[1]
    else:
        prog = re.compile(r"\);", re.MULTILINE)
        found = prog.search(config)
        end_of_conf = found.group(0)
        old_config = config.split(end_of_conf)
        return old_config[0] + "'overwritewebroot' => '/owncloud'\n);" + old_config[1]


class ConfigManager:
    def __init__(self, owncloud_config):
        self.owncloud_config = owncloud_config

    def trusted(self, domain, port):

        if port in [80, 443]:
            optional_port = ""
        else:
            optional_port = ":{0}".format(port)

        self.write(convert_trusted_configuration(self.read(), "{0}{1}".format(domain, optional_port)))

    def overwrite_webroot(self):
        self.write(overwrite_webroot(self.read()))

    def read(self):
        with open(self.owncloud_config, "r") as f:
            return f.read()

    def write(self, config):
        with open(self.owncloud_config, 'w') as f:
            f.write(config)