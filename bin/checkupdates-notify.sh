#!/bin/bash

updates=$(checkupdates | wc -l)

if [ "$updates" -gt 0 ]; then
    notify-send "Updates Available" "$updates packages can be updated."
fi