#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}
BUILD_DIR=${DIR}/../build/snap/signaling

mkdir -p ${BUILD_DIR}/bin

cp -r /usr ${BUILD_DIR}

apt update
apt install -y wget patchelf

# Download forked signaling binary with Unix socket support
ARCH=$(uname -m)
case $ARCH in
  x86_64) ARCH=amd64 ;;
  aarch64) ARCH=arm64 ;;
esac
wget -q https://github.com/cyberb/nextcloud-spreed-signaling/releases/download/v2.0.0-unix/signaling-linux-${ARCH} -O ${BUILD_DIR}/usr/bin/nextcloud-spreed-signaling
chmod +x ${BUILD_DIR}/usr/bin/nextcloud-spreed-signaling

SNAP=/snap/nextcloud/current
mkdir -p $SNAP
ln -s $BUILD_DIR $SNAP/signaling

ldd ${BUILD_DIR}/usr/bin/nextcloud-spreed-signaling

LD=$(echo $SNAP/signaling/usr/lib/*/ld-*.so*)
LIBS=$(echo $SNAP/signaling/usr/lib/*linux*/)

echo "LD: $LD"
echo "LIBS: $LIBS"
patchelf --set-interpreter $LD ${BUILD_DIR}/usr/bin/nextcloud-spreed-signaling
patchelf --set-rpath $LIBS ${BUILD_DIR}/usr/bin/nextcloud-spreed-signaling

${BUILD_DIR}/usr/bin/nextcloud-spreed-signaling --version

cp ${DIR}/bin/* ${BUILD_DIR}/bin/
