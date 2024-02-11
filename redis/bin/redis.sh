#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
LIBS=$(echo ${DIR}/lib/*-linux-gnu*)
exec ${DIR}/lib/*-linux*/ld-*.so.* --library-path $LIBS ${DIR}/usr/local/bin/redis-server "$@"