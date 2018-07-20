#!/bin/sh
sleep 0.5
WS=/home/sindri/bin/ws
MONITOR_COUNT=$(XAUTHORITY=/home/sindri/.Xauthority xrandr --current -d :0| grep connected | grep -v disconnected | wc -l)

CRAZY=$4
echo "CRAZY $CRAZY" >> /tmp/docklogger

if [ "$CRAZY" != "00006030" ]; then
    exit 0
fi

echo "$@" >> /tmp/docklogger
echo "MONITOR_COUNT $MONITOR_COUNT" >> /tmp/docklogger

case "$MONITOR_COUNT" in
    "1")
        XAUTHORITY=/home/sindri/.Xauthority XRANDR_FLAGS="-d :0" $WS single >> /tmp/docklogger 2>&1
        ;;
    "2")
        XAUTHORITY=/home/sindri/.Xauthority XRANDR_FLAGS="-d :0" $WS home >> /tmp/docklogger 2>&1
        ;;
    "3")
        XAUTHORITY=/home/sindri/.Xauthority XRANDR_FLAGS="-d :0" $WS wrk >> /tmp/docklogger 2>&1
        ;;
esac
exit 0