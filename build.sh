#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

BUILD_DIR=${DIR}/build/snap

cp -r bin ${BUILD_DIR}
cp -r config ${BUILD_DIR}
cp -r hooks ${BUILD_DIR}
rm -rf ${BUILD_DIR}/nextcloud/config
ls -la ${BUILD_DIR}/nextcloud/apps

#disable internal updates as they break us
rm -r ${BUILD_DIR}/nextcloud/apps/updatenotification
cat ${BUILD_DIR}/nextcloud/.user.ini
sed -i 's/upload_max_filesize=.*/upload_max_filesize=10G/g' ${BUILD_DIR}/nextcloud/.user.ini
sed -i 's/post_max_size=.*/post_max_size=10G/g' ${BUILD_DIR}/nextcloud/.user.ini
ln -s /var/snap/nextcloud/current/extra-apps ${BUILD_DIR}/nextcloud/extra-apps
