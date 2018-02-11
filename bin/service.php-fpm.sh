#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start]"
    exit 1
fi

export LD_LIBRARY_PATH=${DIR}/php/lib:${DIR}/postgresql/lib

case $1 in
start)
    exec $DIR/php/sbin/php-fpm -y ${SNAP_COMMON}/config/php-fpm.conf -c ${SNAP_COMMON}/config/php.ini
    ;;
post-start)
    timeout 5 /bin/bash -c 'until [ -S '${SNAP_COMMON}'/log/php5-fpm.sock ]; do echo "waiting for ${SNAP_COMMON}/log/php5-fpm.sock"; sleep 1; done'
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac
