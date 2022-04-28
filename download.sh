#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

ARCH=$(uname -m)
DOWNLOAD_URL=https://github.com/syncloud/3rdparty/releases/download/
NEXTCLOUD_VERSION=23.0.2

BUILD_DIR=${DIR}/build/snap
mkdir -p $BUILD_DIR

apt update
apt -y install wget

cd ${DIR}/build
wget -c --progress=dot:giga ${DOWNLOAD_URL}/nginx/nginx-${ARCH}.tar.gz
tar xf nginx-${ARCH}.tar.gz
mv nginx ${BUILD_DIR}

wget --progress=dot:giga https://download.nextcloud.com/server/releases/nextcloud-${NEXTCLOUD_VERSION}.tar.bz2 -O nextcloud.tar.bz2
tar xf nextcloud.tar.bz2
mv nextcloud ${BUILD_DIR}
