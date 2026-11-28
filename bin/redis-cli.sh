#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ "$(whoami)" == "nextcloud" ]]; then
    ${DIR}/redis/bin/redis-cli.sh -s /var/snap/nextcloud/current/redis.sock "$@"
else
    sudo -E -H -u nextcloud ${DIR}/redis/bin/redis-cli.sh -s /var/snap/nextcloud/current/redis.sock "$@"
fi
