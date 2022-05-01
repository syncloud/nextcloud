#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

BUILD_DIR=${DIR}/../build/snap/code
ARCH=$(uname -m)
if [[ $ARCH == "armv7l" ]]; then
    echo "$ARCH is not supported"
    exit 0
fi

docker ps -a -q --filter ancestor=code:syncloud --format="{{.ID}}" | xargs docker stop | xargs docker rm || true
docker rmi code:syncloud || true
docker build -t code:syncloud .
docker create --name=code code:syncloud
mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
docker export code -o app.tar
tar xf app.tar
cp ${DIR}/code.sh ${BUILD_DIR}/bin
rm -rf app.tar
rm -rf ${BUILD_DIR}/usr/src
