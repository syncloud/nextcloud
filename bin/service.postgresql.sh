#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start]"
    exit 1
fi
# shellcheck source=config/env
. "${SNAP_DATA}/config/env"

case $1 in
start)
    exec ${DIR}/postgresql/bin/pg_ctl.sh -w -s -D ${PSQL_DATABASE} start
    ;;
reload)
    exec ${DIR}/postgresql/bin/pg_ctl.sh -s -D ${PSQL_DATABASE} reload
    ;;
stop)
    exec ${DIR}/postgresql/bin/pg_ctl.sh -s -D ${PSQL_DATABASE} stop -m fast
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac
