#!/bin/bash
LG=$(setxkbmap -query | awk '/layout/{print $2}')
if [ "$LG" == "is" ]
then
    setxkbmap -model pc105 -layout us
    echo "Layout: us"
else
    setxkbmap -model pc105 -layout is
    echo "Layout: is"
fi
