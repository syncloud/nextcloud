#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}

MAJOR_VERSION=10

BUILD_DIR=${DIR}/../build/snap/postgresql

docker ps -a -q --filter ancestor=postgres:syncloud --format="{{.ID}}" | xargs docker stop | xargs docker rm || true
docker rmi postgres:syncloud || true
docker build --build-arg MAJOR_VERSION=$MAJOR_VERSION -t postgres:syncloud .
docker run postgres:syncloud postgres --help
docker create --name=postgres postgres:syncloud
mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
echo "${MAJOR_VERSION}" > ${BUILD_DIR}/../db.major.version
docker export postgres -o postgres.tar
tar xf postgres.tar
rm -rf postgres.tar
ls -la 
ls -la bin
ls -la usr/bin
ls -ls usr/share/postgresql-common/pg_wrapper
PGBIN=$(echo usr/lib/postgresql/*/bin)
ldd $PGBIN/initdb || true
mv $PGBIN/postgres $PGBIN/postgres.bin
mv $PGBIN/pg_dump $PGBIN/pg_dump.bin
cp $DIR/bin/* bin
cp $DIR/pgbin/* $PGBIN
