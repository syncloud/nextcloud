#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}
apt update
apt install -y libltdl7 libnss3

BUILD_DIR=${DIR}/build/mail/python
docker ps -a -q --filter ancestor=python:syncloud --format="{{.ID}}" | xargs docker stop | xargs docker rm || true
docker rmi python:syncloud || true
docker build -t python:syncloud -f Dockerfile.python .
docker run python:syncloud python --help
docker create --name=python python:syncloud
mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
docker export python -o python.tar
tar xf python.tar
rm -rf python.tar
cp ${DIR}/bin/python ${BUILD_DIR}/bin/
ls -la ${BUILD_DIR}/bin
rm -rf ${BUILD_DIR}/usr/src
