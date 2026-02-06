#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}
BUILD_DIR=${DIR}/../build/snap/nats
mkdir -p ${BUILD_DIR}

# Download forked nats-server with Unix socket support
ARCH=$(uname -m)
case $ARCH in
  x86_64) ARCH=amd64 ;;
  aarch64) ARCH=arm64 ;;
esac
wget -q https://github.com/cyberb/nats-server/releases/download/v2.14.1-unix/nats-server-linux-${ARCH} -O ${BUILD_DIR}/nats-server
chmod +x ${BUILD_DIR}/nats-server

cp -r ${DIR}/bin ${BUILD_DIR}/
