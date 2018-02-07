#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start]"
    exit 1
fi

case $1 in
start)
    exec ${DIR}/postgresql/bin/pg_ctl -w -s -D ${SNAP_COMMON}/database start
    ;;
post-start)
    if [ -n "$SNAP" ]; then
        PYTHON=/snap/platform/current/python/bin/python
    else
        PYTHON=/opt/app/platform/python/bin/python
    fi
    ${PYTHON} ${DIR}/hooks/postgresql-post-start.py
    ;;
stop)
    exec ${DIR}/postgresql/bin/pg_ctl -s -D ${SNAP_COMMON}/database stop -m fast
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac