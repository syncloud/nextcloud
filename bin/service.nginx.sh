#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

/bin/rm -f ${SNAP_COMMON}/web.socket
/bin/rm -f ${SNAP_COMMON}/log/nginx*.log
exec ${DIR}/nginx/bin/nginx.sh -c ${SNAP_DATA}/config/nginx.conf -p ${DIR}/nginx -e stderr
