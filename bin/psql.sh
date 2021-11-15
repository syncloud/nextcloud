#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [ -z "$SNAP_COMMON" ]; then
  echo "SNAP_COMMON environment variable must be set"
  exit 1
fi

# shellcheck source=config/env
. "${SNAP_DATA}/config/env"

if [[ "$(whoami)" == "nextcloud" ]]; then
    ${DIR}/postgresql/bin/psql.sh -p ${PSQL_PORT} -h ${PSQL_DATABASE} "$@"
else
    sudo -E -H -u nextcloud ${DIR}/postgresql/bin/psql.sh -p ${PSQL_PORT} -h ${PSQL_DATABASE} "$@"
fi
