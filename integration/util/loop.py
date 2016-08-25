from integration.util.ssh import run_ssh


def loop_device_cleanup(num, password):
    print('cleanup')
    for mount in run_ssh('mount', password=password).splitlines():
        if 'loop' in mount:
            print(mount)

    for loop in run_ssh('losetup', password=password).splitlines():
        if 'loop{0}'.format(num) in loop:
            run_ssh('losetup -d /dev/loop{0}'.format(num), throw=False, password=password)

    run_ssh('losetup', password=password)

    for loop in run_ssh('dmsetup ls', password=password).splitlines():
        if 'loop{0}'.format(num) in loop:
            run_ssh('sudo dmsetup remove loop{0}p1'.format(num), password=password)

    for loop_disk in run_ssh('ls -la /tmp', password=password).splitlines():
        if '/tmp/disk{0}'.format(num) in loop_disk:
            run_ssh('rm -fr /tmp/disk{0}'.format(num), throw=False, password=password)


def loop_device_add(fs, dev_num, pasword):

    print('adding loop device')
    run_ssh('dd if=/dev/zero bs=1M count=10 of=/tmp/disk{0}'.format(dev_num), password=pasword)

    run_ssh('losetup /dev/loop{0} /tmp/disk{0}'.format(dev_num), password=pasword)
    run_ssh('file -s /dev/loop{0}'.format(dev_num), password=pasword)
    run_ssh('mkfs.{0} /dev/loop{1}'.format(fs, dev_num), password=pasword)
    return '/dev/loop{0}'.format(dev_num)
