#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [[ -z "$2" ]]; then
    echo "usage $0 app version"
    exit 1
fi

NAME=$1
VERSION=$2
ARCH=$(dpkg --print-architecture)

SNAP_DIR=${DIR}/build/snap

apt update
apt -y install squashfs-tools

cp -r ${DIR}/bin ${SNAP_DIR}
cp -r ${DIR}/config ${SNAP_DIR}
cp -r ${DIR}/hooks ${SNAP_DIR}
cp -r ${DIR}/meta ${SNAP_DIR}

echo "version: $VERSION" >> ${SNAP_DIR}/meta/snap.yaml
echo "architectures:" >> ${SNAP_DIR}/meta/snap.yaml
echo "- ${ARCH}" >> ${SNAP_DIR}/meta/snap.yaml

PACKAGE=${NAME}_${VERSION}_${ARCH}.snap
echo ${PACKAGE} > ${DIR}/package.name
mksquashfs ${SNAP_DIR} ${DIR}/${PACKAGE} -noappend -comp xz -no-xattrs -all-root
mkdir ${DIR}/artifact
cp ${DIR}/${PACKAGE} ${DIR}/artifact
