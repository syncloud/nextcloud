import subprocess

print(subprocess.check_output('snap run nextcloud.access-change', shell=True))

