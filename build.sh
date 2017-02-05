#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp

NAME=nextcloud
NEXTCLOUD_VERSION=11.0.1
COIN_CACHE_DIR=${DIR}/coin.cache
ARCH=$(dpkg-architecture -qDEB_HOST_GNU_CPU)
if [ ! -z "$1" ]; then
    ARCH=$1
fi

VERSION="local"
if [ ! -z "$2" ]; then
    VERSION=$2
fi

./coin_lib.sh

cp -r ${DIR}/src lib/syncloud-owncloud-${VERSION}

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

DOWNLOAD_URL=http://build.syncloud.org:8111/guestAuth/repository/download

coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_php_${ARCH}/lastSuccessful/php-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_nginx_${ARCH}/lastSuccessful/nginx-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_postgresql_${ARCH}/lastSuccessful/postgresql-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw https://download.nextcloud.com/server/releases/${NAME}-${NEXTCLOUD_VERSION}.tar.bz2

cp -r bin ${BUILD_DIR}
cp -r config ${BUILD_DIR}/config.templates
cp -r lib ${BUILD_DIR}

rm -rf ${BUILD_DIR}/${NAME}/config

mkdir build/${NAME}/META
echo ${NAME} >> build/${NAME}/META/app
echo ${VERSION} >> build/${NAME}/META/version

echo "zipping"
tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}
