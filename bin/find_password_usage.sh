#!/usr/bin/env bash
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 my-possibly-compromised-password"
    exit 1;
fi

ALL_IDS=`lpass ls | grep "^\S" | rev | cut -d" " -f1 | rev | sed 's/[^[0-9]*//g'`

for id in $ALL_IDS; do
    password=`lpass show --password $id`
    if [[ "$1" == "$password" ]]; then
        lpass show $id
    fi
done
