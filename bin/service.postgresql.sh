#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

. "${SNAP_DATA}/config/env"
exec ${DIR}/postgresql/bin/pg_ctl.sh -w -s -D ${PSQL_DATABASE} start
