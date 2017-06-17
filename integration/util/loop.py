from integration.util.ssh import run_ssh


def loop_device_cleanup(host, dev_file, password):
    print('cleanup')
    for mount in run_ssh(host, 'mount', password=password).splitlines():
        if dev_file in mount:
            print(mount)
            for i in range(0, 20):
                if 'loop{0}'.format(i) in mount:
                    run_ssh(host, 'umount /dev/loop{0}'.format(i), throw=False, password=password)

    for loop in run_ssh(host, 'losetup', password=password).splitlines():
        if dev_file in loop or 'deleted' in loop:
            for i in range(0, 20):
                if 'loop{0}'.format(i) in loop:
                    run_ssh(host, 'losetup -d /dev/loop{0}'.format(i), throw=False, password=password) 

    run_ssh(host, 'losetup', password=password)

    for loop in run_ssh(host, 'dmsetup ls', password=password).splitlines():
        if 'loop0p1' in loop:
            run_ssh(host, 'sudo dmsetup remove loop0p1', password=password)
        if 'loop0p2' in loop:
            run_ssh(host, 'sudo dmsetup remove loop0p2', password=password)

    run_ssh(host, 'rm -rf {0}'.format(dev_file), throw=False, password=password)


def loop_device_add(host, fs, dev_file, password):
    print('adding loop device')
    run_ssh(host, 'dd if=/dev/zero bs=1M count=10 of={0}'.format(dev_file), password=password)
    loop = run_ssh(host, 'losetup -f --show {0}'.format(dev_file), password=password)
    run_ssh(host, 'file -s {0}'.format(loop), password=password) 
    run_ssh(host, 'mkfs.{0} {1}'.format(fs, loop), password=password)
    return loop 
