#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
LIBS=${DIR}/lib/*linux*
exec ${DIR}/lib/*/ld-*.so --library-path $LIBS ${DIR}/usr/lib/postgresql/*/bin/initdb "$@"

