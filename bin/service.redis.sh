#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
exec $DIR/redis/bin/redis.sh ${SNAP_DATA}/config/redis.conf