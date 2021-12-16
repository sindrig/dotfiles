#!/usr/bin/env bash
while true; do notify-send "Skráðu tímana þína haugurinn þinn <3" && sleep $(( 30 * 60 + $RANDOM % (30 * 60))); done
