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
    exec $DIR/code/bin/code.sh --version --o:sys_template_path=$SNAP_DATA/code/systemplate --o:child_root_path=$SNAP_DATA/code/child-roots --o:file_server_root_path=$SNAP_DATA/code/coolwsd --o:logging.color=false --o:ssl.enable=false
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac
