#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}
BUILD_DIR=${DIR}/../build/snap/nextcloud
mkdir -p $BUILD_DIR
cp -r /usr/src/nextcloud/. ${BUILD_DIR}/
