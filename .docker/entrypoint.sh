#!/bin/sh

mkdir /app/data/logs/ -p

. /etc/apache2/envvars
exec apache2 -D FOREGROUND