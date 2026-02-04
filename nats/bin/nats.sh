#!/bin/sh -e
DIR=$( cd "$( dirname "$0" )" && cd .. && pwd )
exec ${DIR}/nats-server "$@"
