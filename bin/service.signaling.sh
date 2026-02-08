#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
exec $DIR/signaling/bin/signaling.sh -config ${SNAP_DATA}/config/signaling.conf
