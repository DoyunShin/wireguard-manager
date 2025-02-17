#!/bin/sh

sudo mkdir /app/data/logs/ -p
sudo rm -f /usr/local/apache2/logs/httpd.pid

. /usr/local/apache2/bin/envvars
sudo -E /usr/local/apache2/bin/httpd -D FOREGROUND "$@"
# exec apache2 -D FOREGROUND
