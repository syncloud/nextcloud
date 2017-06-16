#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [[ -z "$1" || -z "$2" ]]; then
    echo "usage $0 app_arch app_version"
    exit 1
fi

export TMPDIR=/tmp
export TMP=/tmp

NAME=nextcloud
NEXTCLOUD_VERSION=11.0.2
COIN_CACHE_DIR=${DIR}/coin.cache
ARCH=$1
VERSION=$2

rm -rf ${DIR}/lib
mkdir ${DIR}/lib

coin --to lib py https://pypi.python.org/packages/2.7/b/beautifulsoup4/beautifulsoup4-4.4.0-py2-none-any.whl
coin --to lib py https://pypi.python.org/packages/2.7/r/requests/requests-2.7.0-py2.py3-none-any.whl
coin --to lib py https://pypi.python.org/packages/source/m/massedit/massedit-0.67.1.zip
coin --to lib py https://pypi.python.org/packages/source/s/syncloud-lib/syncloud-lib-2.tar.gz

cp -r ${DIR}/src lib/syncloud-${NAME}-${VERSION}

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
