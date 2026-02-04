#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}
BUILD_DIR=${DIR}/../build/snap/nats
mkdir -p ${BUILD_DIR}
cp /usr/local/bin/nats-server ${BUILD_DIR}/
cp -r ${DIR}/bin ${BUILD_DIR}/
