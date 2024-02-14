#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}
VERSION=$1
BUILD_DIR=${DIR}/../build/snap/nginx
while ! docker create --name=nginx nginx:$VERSION ; do
  sleep 1
  echo "retry docker"
done
mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
docker export nginx -o app.tar
tar xf app.tar
rm -rf app.tar
cp ${DIR}/nginx.sh ${BUILD_DIR}/bin/
