#!/bin/bash
LG=$(setxkbmap -query | awk '/layout/{print $2}')
if [ "$LG" == "is" ]
then
    setxkbmap us
    echo "Layout: us"
else
    setxkbmap is
    echo "Layout: is"
fi
