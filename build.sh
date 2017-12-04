#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [[ -z "$2" ]]; then
    echo "usage $0 version installer"
    exit 1
fi

export TMPDIR=/tmp
export TMP=/tmp

NAME=nextcloud
NEXTCLOUD_VERSION=12.0.3
COIN_CACHE_DIR=${DIR}/coin.cache
ARCH=$(uname -m)
VERSION=$1
INSTALLER=$2

rm -rf ${DIR}/lib
mkdir ${DIR}/lib

coin --to lib py https://pypi.python.org/packages/2.7/b/beautifulsoup4/beautifulsoup4-4.4.0-py2-none-any.whl
coin --to lib py https://pypi.python.org/packages/ea/03/92d3278bf8287c5caa07dbd9ea139027d5a3592b0f4d14abf072f890fab2/requests-2.11.1-py2.py3-none-any.whl#md5=b4269c6fb64b9361288620ba028fd385
coin --to lib py https://pypi.python.org/packages/f3/94/67d781fb32afbee0fffa0ad9e16ad0491f1a9c303e14790ae4e18f11be19/requests-unixsocket-0.1.5.tar.gz#md5=08453c8ef7dc03863ff4a30b901e7c20
coin --to lib py https://pypi.python.org/packages/source/m/massedit/massedit-0.67.1.zip
coin --to lib py https://pypi.python.org/packages/b1/f3/732948155aff67497d16966ed9ecadfc1103a37f2b7fb7e93c443a12510c/syncloud-lib-16.tar.gz#md5=7c555868248f977acb51eb4e9e520f4e

cp -r ${DIR}/src lib/syncloud-${NAME}-${VERSION}

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

DOWNLOAD_URL=http://artifact.syncloud.org/3rdparty

coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/php7-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/nginx-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/postgresql-${ARCH}.tar.gz
#coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/python-${ARCH}.tar.gz

coin --to ${BUILD_DIR} raw https://download.nextcloud.com/server/releases/${NAME}-${NEXTCLOUD_VERSION}.tar.bz2
mv ${BUILD_DIR}/php7 ${BUILD_DIR}/php

cp -r bin ${BUILD_DIR}
cp -r config ${BUILD_DIR}/config.templates
cp -r lib ${BUILD_DIR}

rm -rf ${BUILD_DIR}/${NAME}/config
ls -la ${BUILD_DIR}/${NAME}/apps

#disable internal updates as they break us
rm -r ${BUILD_DIR}/${NAME}/apps/updatenotification

mkdir build/${NAME}/META
echo ${NAME} >> build/${NAME}/META/app
echo ${VERSION} >> build/${NAME}/META/version

if [ $INSTALLER == "sam" ]; then

    echo "zipping"
    rm -rf ${NAME}*.tar.gz
    tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}

else

    echo "snapping"
    SNAP_DIR=${DIR}/build/snap
    ARCH=$(dpkg-architecture -q DEB_HOST_ARCH)
    rm -rf ${DIR}/*.snap
    mkdir ${SNAP_DIR}
    cp -r ${BUILD_DIR}/* ${SNAP_DIR}/
    cp -r ${DIR}/snap/meta ${SNAP_DIR}/
    cp ${DIR}/snap/snap.yaml ${SNAP_DIR}/meta/snap.yaml
    echo "version: $VERSION" >> ${SNAP_DIR}/meta/snap.yaml
    echo "architectures:" >> ${SNAP_DIR}/meta/snap.yaml
    echo "- ${ARCH}" >> ${SNAP_DIR}/meta/snap.yaml

    mksquashfs ${SNAP_DIR} ${DIR}/${NAME}_${VERSION}_${ARCH}.snap -noappend -comp xz -no-xattrs -all-root

fi