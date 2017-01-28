#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

export LD_LIBRARY_PATH=${DIR}/php/lib:${DIR}/postgresql/lib

exec $DIR/php/sbin/php-fpm -y ${DIR}/config/php/php-fpm.conf -c ${DIR}/config/php/php.ini
