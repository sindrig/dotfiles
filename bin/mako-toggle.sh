#!/bin/bash

if pgrep -x mako > /dev/null; then
    notify-send "🔕 Pausing notifications"
    sleep 1
    pkill mako
else
    mako & disown
    notify-send "🔔 Notifications resumed"
fi

