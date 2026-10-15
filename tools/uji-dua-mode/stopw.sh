#!/bin/bash
for p in $(pgrep -x php); do tr '\0' ' ' < /proc/$p/cmdline | grep -q "wa_worker" && kill $p; done; true
