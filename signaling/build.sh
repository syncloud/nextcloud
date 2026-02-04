#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}
BUILD_DIR=${DIR}/../build/snap/signaling
docker ps -a
docker build --file Dockerfile -t signaling .
docker create --name=signaling signaling
mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
docker export signaling -o signaling.tar
tar xf signaling.tar
rm -rf signaling.tar
docker rm signaling
cp ${DIR}/bin/* ${BUILD_DIR}/bin/
