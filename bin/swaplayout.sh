#!/usr/bin/env bash
set -euo pipefail

KEYBOARD="1:1:AT_Translated_Set_2_keyboard"
LG=$(swaymsg -t get_inputs | jq -r '.[] | select(.identifier == "'"$KEYBOARD"'") | .xkb_active_layout_name')
if [ "$LG" == "Icelandic" ]
then
    swaymsg input "$KEYBOARD" xkb_layout us -q
    echo "Layout: us"
else
    swaymsg input "$KEYBOARD" xkb_layout is -q
    echo "Layout: is"
fi
