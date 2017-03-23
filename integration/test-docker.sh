#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [[ -z "$1" || -z "$2" || -z "$3" || -z "$4" || -z "$5" ]]; then
    echo "usage $0 redirect_user redirect_password redirect_domain release app_archive_path"
    exit 1
fi

./docker.sh

apt-get install -y sshpass owncloud-client-cmd firefox xvfb
coin --to ${DIR} raw --subfolder geckodriver https://github.com/mozilla/geckodriver/releases/download/v0.9.0/geckodriver-v0.9.0-linux64.tar.gz
mv ${DIR}/geckodriver/geckodriver ${DIR}/geckodriver/wires

${DIR}/../coin_lib.sh

pip2 install -r ${DIR}/../src/dev_requirements.txt
pip2 install -U pytest
xvfb-run --server-args="-screen 0, 1024x768x24" py.test -x -s verify.py test_ui.py --email=$1 --password=$2 --domain=$3 --release=$4 --app_archive_path=$5