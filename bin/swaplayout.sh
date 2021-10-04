#!/usr/bin/env bash
set -euo pipefail

LG=$(swaymsg -t get_inputs | jq -r '.[].xkb_active_layout_name' | sed -e '/^null$/d' | uniq)
if [ "$LG" == "Icelandic" ]
then
    swaymsg input '*' xkb_layout us -q
    echo "Layout: us"
else
    swaymsg input '*' xkb_layout is -q
    echo "Layout: is"
fi
