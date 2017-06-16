#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [ -z "$1" ]; then
    echo "usage: $0 arch"
fi

ARCH=$1
APP=nextcloud
docker build -f Dockerfile.deps.$ARCH -t syncloud/$APP-build-deps-$ARCH .
docker push syncloud/$APP-build-deps-$ARCH
