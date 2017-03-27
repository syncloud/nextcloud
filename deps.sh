#!/bin/bash -xe

apt-get install -y dpkg-dev
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py
pip install coin
ARCH=$(dpkg-architecture -q DEB_HOST_ARCH)
if [ $ARCH == "amd64" ]; then
  wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2
  tar xjvf phantomjs-2.1.1-linux-x86_64.tar.bz2
  cp ./phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/bin
else
  wget https://github.com/fg2it/phantomjs-on-raspberry/releases/download/v2.1.1-wheezy-jessie-armv6/phantomjs
  cp phantomjs /usr/bin
fi
chmod +x /usr/bin/phantomjs