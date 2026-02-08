#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}
BUILD_DIR=${DIR}/../build/snap/signaling
$BUILD_DIR/bin/signaling.sh --version
