#!/bin/bash

LG=$(setxkbmap -query | awk '/layout/{print $2}')
echo $LG
echo $LG
if [ $LG == "is" ]
then
    echo \#009E00
else
    echo \#57F7F5
fi
