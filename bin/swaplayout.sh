#!/usr/bin/env bash
set -euo pipefail

KEYBOARDS=('1578:14516:MosArt_M32_0022_Varmilo' '1:1:AT_Translated_Set_2_keyboard' '1241:17733:USB_Keyboard')

new_layout=is
for keyboard in "${KEYBOARDS[@]}"; do
    LG=$(swaymsg -t get_inputs | jq -r '.[] | select(.identifier == "'"$keyboard"'") | .xkb_layout_names[0]' )
    if [[ "$LG" != "" ]]; then
        if [[ "$LG" == "Icelandic"* ]]; then
            new_layout=us
        fi
        break
    fi
done

for keyboard in "${KEYBOARDS[@]}"; do
    swaymsg input "$keyboard" xkb_layout "$new_layout" -q
done

echo $BASHPID >> /home/sindri/pidstore
