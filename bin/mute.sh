#!/bin/bash

VOLFILE=/home/sindri/.cache/last_volume

amixer-with-output() {
    vol=$(amixer "$@" | grep 'Front Left: Playback' | awk '{print $5}')
    vol=${vol#"["}
    vol=${vol%"]"}
    vol=${vol%"%"}
    echo $vol
}

notify() {
    notify-send -t 750 "$@"
}

current=$(amixer-with-output -D pulse sget Master)

if [ $current -eq 0 ]; then
    if [ -f $VOLFILE ]; then
        new_volume=$(cat $VOLFILE)
        rm $VOLFILE
        notify "Unmuted" [$(amixer-with-output -D pulse sset Master "$new_volume%")%]
    fi
else
    echo $(amixer-with-output -D pulse sget Master) > $VOLFILE
    amixer-with-output -D pulse sset Master 0% > /dev/null
    notify "Muted"
fi