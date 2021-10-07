#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [[ -z "$2" ]]; then
    echo "usage $0 name version"
    exit 1
fi

export TMPDIR=/tmp
export TMP=/tmp

NAME=$1
NEXTCLOUD_VERSION=22.2.0
ARCH=$(uname -m)
VERSION=$2
DB_MAJOR_VERSION=10

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

DOWNLOAD_URL=https://github.com/syncloud/3rdparty/releases/download/1

wget --progress=dot:giga ${DOWNLOAD_URL}/php7-${ARCH}.tar.gz
tar xf php7-${ARCH}.tar.gz
mv php ${BUILD_DIR}/

wget --progress=dot:giga ${DOWNLOAD_URL}/nginx-${ARCH}.tar.gz
tar xf nginx-${ARCH}.tar.gz
mv nginx ${BUILD_DIR}/

wget --progress=dot:giga ${DOWNLOAD_URL}/postgresql-${DB_MAJOR_VERSION}-${ARCH}.tar.gz
tar xf postgresql-${DB_MAJOR_VERSION}-${ARCH}.tar.gz
mv postgresql-${DB_MAJOR_VERSION} ${BUILD_DIR}/postgresql
echo "${DB_MAJOR_VERSION}" > ${BUILD_DIR}/db.major.version
wget --progress=dot:giga ${DOWNLOAD_URL}/python-${ARCH}.tar.gz
tar xf python-${ARCH}.tar.gz
mv python ${BUILD_DIR}/

wget --progress=dot:giga https://download.nextcloud.com/server/releases/${NAME}-${NEXTCLOUD_VERSION}.tar.bz2
tar xf ${NAME}-${NEXTCLOUD_VERSION}.tar.bz2
mv nextcloud ${BUILD_DIR}/

${BUILD_DIR}/python/bin/pip install -r ${DIR}/requirements.txt

cp -r bin ${BUILD_DIR}
cp -r config ${BUILD_DIR}/config.templates
cp -r hooks ${BUILD_DIR}
rm -rf ${BUILD_DIR}/${NAME}/config
ls -la ${BUILD_DIR}/${NAME}/apps

#disable internal updates as they break us
rm -r ${BUILD_DIR}/${NAME}/apps/updatenotification

mkdir build/${NAME}/META
echo ${NAME} >> build/${NAME}/META/app
echo ${VERSION} >> build/${NAME}/META/version

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
mkdir ${DIR}/artifact
cp ${DIR}/${PACKAGE} ${DIR}/artifact
