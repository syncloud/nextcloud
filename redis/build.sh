#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}
BUILD_DIR=${DIR}/../build/snap/redis
mkdir $BUILD_DIR
cp -r /usr ${BUILD_DIR}
cp -r /lib ${BUILD_DIR}
cp -r ${DIR}/bin ${BUILD_DIR}/bin
