#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export LC_ALL=C
exec ${DIR}/php/lib/ld.so --library-path ${DIR}/php/lib:${DIR}/php/lib/private ${DIR}/php/bin/php "$@"