#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [[ -z "$1" ]]; then
    echo "usage $0 version"
    exit 1
fi

export TMPDIR=/tmp
export TMP=/tmp

NAME=nextcloud
NEXTCLOUD_VERSION=14.0.3
COIN_CACHE_DIR=${DIR}/coin.cache
ARCH=$(uname -m)
VERSION=$1
INSTALLER=$2

rm -rf ${DIR}/lib
mkdir ${DIR}/lib

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

DOWNLOAD_URL=http://artifact.syncloud.org/3rdparty

coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/php7-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/nginx-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/postgresql-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/python-${ARCH}.tar.gz

${BUILD_DIR}/python/bin/pip install -r ${DIR}/requirements.txt

coin --to ${BUILD_DIR} raw https://download.nextcloud.com/server/releases/${NAME}-${NEXTCLOUD_VERSION}.tar.bz2
mv ${BUILD_DIR}/php7 ${BUILD_DIR}/php

cp -r bin ${BUILD_DIR}
cp -r config ${BUILD_DIR}/config.templates
cp -r lib ${BUILD_DIR}
cp -r hooks ${BUILD_DIR}
rm -rf ${BUILD_DIR}/${NAME}/config
ls -la ${BUILD_DIR}/${NAME}/apps

#disable internal updates as they break us
rm -r ${BUILD_DIR}/${NAME}/apps/updatenotification

mkdir build/${NAME}/META
echo ${NAME} >> build/${NAME}/META/app
echo ${VERSION} >> build/${NAME}/META/version

#sed -i 's/allowSymlinks = false/allowSymlinks = true/g' ${BUILD_DIR}/${NAME}/lib/private/Files/Storage/Local.php
cat ${BUILD_DIR}/${NAME}/.user.ini
sed -i 's/upload_max_filesize=.*/upload_max_filesize=10G/g' ${BUILD_DIR}/${NAME}/.user.ini
sed -i 's/post_max_size=.*/post_max_size=10G/g' ${BUILD_DIR}/${NAME}/.user.ini
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

PACKAGE=${NAME}_${VERSION}_${ARCH}.snap
echo ${PACKAGE} > package.name
mksquashfs ${SNAP_DIR} ${DIR}/${PACKAGE} -noappend -comp xz -no-xattrs -all-root
