#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

MAJOR_VERSION=10

apt update
apt install -y libltdl7 libnss3

BUILD_DIR=${DIR}/../build/nextcloud/postgresql

docker ps -a -q --filter ancestor=postgres:syncloud --format="{{.ID}}" | xargs docker stop | xargs docker rm || true
docker rmi postgres:syncloud || true
docker build --build-arg MAJOR_VERSION=$MAJOR_VERSION -t postgres:syncloud .
docker run postgres:syncloud postgres --help
docker create --name=postgres postgres:syncloud
mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
echo "${MAJOR_VERSION}" > ${BUILD_DIR}/db.major.version
docker export postgres -o postgres.tar
tar xf postgres.tar
rm -rf postgres.tar
ls -la 
ls -la bin
ls -la usr/bin

DIR}/postgres ${BUILD_DIR}/bin/postgresql
ls -la ${BUILD_DIR}/bin
rm -rf ${BUILD_DIR}/usr/src
