#!/bin/bash

envs=('ids-prod' 'prod' 'dev' 'staging' 'shared')
pids=()
for i in ${envs[*]}; do
    aws sso login --profile ${i} &
    pids+=($!)
done

for pid in ${pids[*]}; do
    echo "Waiting for $pid"
    wait ${pid}
    echo "$pid done!"
done

echo "Finished all logins"
aws ecr get-login-password --profile=shared | docker login --username AWS --password-stdin 821090935708.dkr.ecr.eu-west-1.amazonaws.com
echo
