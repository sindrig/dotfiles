#!/usr/bin/env bash

if [ "$#" -ne 2 ]; then
    echo "Usage: create_sublime_project.sh PROJECT_NAME PROJECT_DIRECTORY"
    exit 1
fi

PROJECT_NAME=$1
PROJECT_DIRECTORY="$( cd $2 && pwd )"

SUBLIME_PROJECT_DIRECTORY="~/dev/Projects/"
TARGET_FILENAME="$SUBLIME_PROJECT_DIRECTORY$PROJECT_NAME.sublime-project"
eval TARGET_FILENAME=$TARGET_FILENAME

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SAMPLE_FILENAME="sample-project.sublime-project"

PROJECT_CONTENTS=$(cat $DIR/$SAMPLE_FILENAME | sed "s_PATH\_TO\_PROJECT_$2_")
echo $TARGET_FILENAME
echo "$PROJECT_CONTENTS" > "$TARGET_FILENAME"
