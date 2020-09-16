#!/bin/sh

notify-send "$(baton status)" >> ~/.current-spotify-song.log 2>&1