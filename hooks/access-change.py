import subprocess
from os.path import join, dirname

subprocess.check_output(join(dirname(__file__), 'access-change'), shell=True)

