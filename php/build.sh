#!/bin/sh -xe

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}

BUILD_DIR=${DIR}/../build/snap/php

docker ps -a -q --filter ancestor=php:syncloud --format="{{.ID}}" | xargs docker stop | xargs docker rm || true
docker rmi php:syncloud || true
docker build -t php:syncloud .
docker run php:syncloud php -i
docker create --name=php php:syncloud
mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
docker export php -o php.tar
tar xf php.tar
rm -rf php.tar
mv ${BUILD_DIR}/usr/lib/*-linux*/ImageMagick-*/modules-*/coders ${BUILD_DIR}/usr/lib/ImageMagickCoders
ls -la ${BUILD_DIR}/usr/lib/ImageMagickCoders
cp ${DIR}/php.sh ${BUILD_DIR}/bin
cp ${DIR}/php-fpm.sh ${BUILD_DIR}/bin
mkdir -p ${BUILD_DIR}/lib/php/extensions
mv ${BUILD_DIR}/usr/local/lib/php/extensions/*/*.so ${BUILD_DIR}/lib/php/extensions
rm -rf ${BUILD_DIR}/usr/src
