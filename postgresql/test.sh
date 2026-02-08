#!/bin/bash -xe

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}

BUILD_DIR=${DIR}/../build/snap/postgresql
cd ${BUILD_DIR}
PGBIN=$(echo usr/lib/postgresql/*/bin)
ldd $PGBIN/initdb || true
./bin/initdb.sh --help
