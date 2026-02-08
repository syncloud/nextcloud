#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
exec $DIR/nats/bin/nats.sh -c ${SNAP_DATA}/config/nats.conf
