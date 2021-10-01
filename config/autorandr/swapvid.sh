#!/usr/bin/env bash

DIR="$(dirname "$(readlink -f "$0")")"

cat $DIR/*/config | grep 'DP-' > /dev/null
fromintel=$?
echo "From intel: $fromintel"
set -e

for f in $DIR/*/config; do
    if [[ fromintel -eq 0 ]]; then
        sed -i 's/DP-*/DP/' $f
    else
        sed -i 's/DP/DP-/' $f
    fi
done