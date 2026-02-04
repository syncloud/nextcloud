#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
exec $DIR/php/bin/php-fpm.sh \
  -y ${SNAP_DATA}/config/php-fpm.conf \
  -c ${SNAP_DATA}/config/php.ini
