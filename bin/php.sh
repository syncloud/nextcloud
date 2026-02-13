#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
SNAP_DATA=/var/snap/nextcloud/current
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LC_TIME=en_US.UTF-8
export NEXTCLOUD_CONFIG_DIR=${SNAP_DATA}/nextcloud/config
exec $DIR/php/bin/php.sh -c ${SNAP_DATA}/config/php.ini "$@"
