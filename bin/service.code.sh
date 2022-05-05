#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start]"
    exit 1
fi
ARCH=$(uname -m)
case $1 in
start)
    if [[ $ARCH == "armv7l" ]]; then
        echo "$ARCH is not supported"
        exit 0
    fi
    exec $DIR/code/bin/code.sh --disable-cool-user-checking --lo-template-path=$SNAP/code/opt/collaboraoffice --version --config-file=$SNAP_DATA/config/code/coolwsd.xml
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac
