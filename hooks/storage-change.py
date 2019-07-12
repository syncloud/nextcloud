import subprocess

print(subprocess.check_output('snap run nextcloud.storage-change', shell=True))
