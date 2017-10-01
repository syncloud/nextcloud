#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
if [[ -z "$1" ]]; then
    echo "usage $0 config_dir"
    exit 1
fi
CONFIG_DIR=$1
export LD_LIBRARY_PATH=${DIR}/php/lib:${DIR}/postgresql/lib

exec $DIR/php/sbin/php-fpm -y ${CONFIG_DIR}/php-fpm.conf -c ${CONFIG_DIR}/php.ini
