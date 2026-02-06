#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}
BUILD_DIR=${DIR}/../build/snap/nats
mkdir -p ${BUILD_DIR}

cp -r /usr ${BUILD_DIR}

apt update
apt install -y wget patchelf

# Download forked nats-server with Unix socket support
ARCH=$(uname -m)
case $ARCH in
  x86_64) ARCH=amd64 ;;
  aarch64) ARCH=arm64 ;;
esac
wget -q https://github.com/cyberb/nats-server/releases/download/v2.14.1-unix/nats-server-linux-${ARCH} -O ${BUILD_DIR}/nats-server
chmod +x ${BUILD_DIR}/nats-server

SNAP=/snap/nextcloud/current
mkdir -p $SNAP
ln -s $BUILD_DIR $SNAP/nats

ldd ${BUILD_DIR}/nats-server

LD=$(echo $SNAP/nats/usr/lib/*/ld-*.so*)
LIBS=$(echo $SNAP/nats/usr/lib/*linux*/)

echo "LD: $LD"
echo "LIBS: $LIBS"
patchelf --set-interpreter $LD ${BUILD_DIR}/nats-server
patchelf --set-rpath $LIBS ${BUILD_DIR}/nats-server

${BUILD_DIR}/nats-server --version

cp -r ${DIR}/bin ${BUILD_DIR}/
