#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
LIBS=$(echo ${DIR}/usr/lib/*-linux-gnu*)
exec ${DIR}/usr/lib/*-linux*/ld-*.so.* --library-path $LIBS ${DIR}/nats-server "$@"
