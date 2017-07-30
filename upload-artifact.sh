#!/bin/bash -e

if [ -z "$ARTIFACT_SSH_KEY" ]; then
  echo "ARTIFACT_SSH_KEY must be set"
  exit 1
fi

if [ -z "$2" ]; then
  echo "usage $0 src dst"
  exit 1
fi

if [ ! -d $1 ]; then
    echo "nothing to upload, $1 does not exist"
    exit 0
fi
APP=nextcloud
echo "$ARTIFACT_SSH_KEY" | base64 --decode > artifact_ssh.key
chmod 600 artifact_ssh.key
chmod -R a+r $1
scp -r -oStrictHostKeyChecking=no -i artifact_ssh.key $1 artifact@artifact.syncloud.org:/home/artifact/repo/$APP/ci/$2
