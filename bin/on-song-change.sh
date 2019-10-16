#!/bin/sh

status=$(baton status)
song_name=`echo "$status" | grep '^Track' | cut -d" " -f2-`
artist=`echo "$status" | grep '^Artist' | cut -d" " -f2-`
echo "$song_name by $artist" > ~/.current-spotify-song
echo "$song_name by $artist" > ~/.current-spotify-song