#!/bin/bash
# srv.sh <dir> <port>: (re)start php -S untuk app uji
P=$2; for pid in $(ss -ltnp "sport = :$P" | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u); do kill $pid; done; sleep 0.3
cd "$(dirname "$0")/$1" && (PHP_CLI_SERVER_WORKERS=8 php -S 127.0.0.1:$P >/tmp/srv-$P.log 2>&1 &); sleep 0.7
