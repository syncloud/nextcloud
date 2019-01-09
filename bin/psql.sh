#!/usr/bin/env bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [ -z "SNAP_COMMON" ]; then
  echo "SNAP_COMMON environment variable must be set"
  exit 1
fi

. ${SNAP_COMMON}/config/env

sudo -E -H -u nextcloud ${DIR}/postgresql/bin/psql -p $PSQL_PORT -h ${SNAP_COMMON}/database "$@"
