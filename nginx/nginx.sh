#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
LIBS=$(echo ${DIR}/lib/*-linux-gnu* ${DIR}/usr/lib/*-linux-gnu* | tr ' ' ':')
LOADER=$(ls ${DIR}/lib/*-linux-gnu*/ld-linux*.so* ${DIR}/lib/ld-linux*.so* 2>/dev/null | head -1)
exec "${LOADER}" --library-path "${LIBS}" ${DIR}/usr/sbin/nginx "$@"
