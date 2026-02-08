#!/bin/sh -xe

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}

BUILD_DIR=${DIR}/../build/snap/postgresql

mkdir -p ${BUILD_DIR}

rm -rf usr/lib/*/perl
rm -rf usr/lib/*/perl-base
rm -rf usr/lib/*/dri
rm -rf usr/lib/*/mfx
rm -rf usr/lib/*/vdpau
rm -rf usr/lib/*/gconv
rm -rf usr/lib/*/lapack
rm -rf usr/lib/gcc
rm -rf usr/lib/git-core

cp -r /usr ${BUILD_DIR}
cp -r /lib ${BUILD_DIR}

PGBIN=$(echo ${BUILD_DIR}/usr/lib/postgresql/*/bin)
MAJOR_VERSION=$(basename $(dirname $PGBIN))
echo "${MAJOR_VERSION}" > ${BUILD_DIR}/../db.major.version
mv $PGBIN/postgres $PGBIN/postgres.bin
mv $PGBIN/pg_dump $PGBIN/pg_dump.bin
mkdir ${BUILD_DIR}/bin
cp $DIR/bin/* ${BUILD_DIR}/bin
cp $DIR/pgbin/* $PGBIN
