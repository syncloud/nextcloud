#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}
VERSION=$1
BUILD_DIR=${DIR}/../build/snap/nats
while ! docker create --name=nats nats:$VERSION ; do
  sleep 1
  echo "retry docker"
done
mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
docker export nats -o app.tar
tar xf app.tar
rm -rf app.tar
mkdir -p ${BUILD_DIR}/bin
cp -f ${DIR}/bin/* ${BUILD_DIR}/bin
