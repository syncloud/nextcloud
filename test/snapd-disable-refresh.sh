#!/bin/sh
set -e
mkdir -p /etc/systemd/system/snapd.service.d
cp test/snapd-disable-refresh.conf /etc/systemd/system/snapd.service.d/disable-refresh.conf
