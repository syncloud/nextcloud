#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [ -z "$SNAP_COMMON" ]; then
  echo "SNAP_COMMON environment variable must be set"
  exit 1
fi

# shellcheck source=config/env
. "${SNAP_DATA}/config/env"
export LD_LIBRARY_PATH=${DIR}/postgresql/lib

if [[ "$(whoami)" == "nextcloud" ]]; then
    ${DIR}/postgresql/bin/initdb "$@"
else
    sudo -E -H -u nextcloud LD_LIBRARY_PATH=${LD_LIBRARY_PATH} ${DIR}/postgresql/bin/initdb "$@"
fi
