#!/bin/bash

customer=${1:-island}
case $customer in
    island)
        envs=('ids-prod' 'prod' 'dev' 'staging' 'shared')
        ;;
    mms)
        envs=('prod' 'dev' 'staging' 'shared')
        ;;
    *)
        echo "Unknown customer $customer"
        ;;
esac

pids=()
for i in ${envs[*]}; do
    aws sso login --profile $customer-${i} &
    pids+=($!)
done

for pid in ${pids[*]}; do
    echo "Waiting for $pid"
    wait ${pid}
    echo "$pid done!"
done

echo "Finished all logins"
sharedaccountid=$(aws sts get-caller-identity --profile=$customer-shared --query=Account --output=text)
aws ecr get-login-password --profile=$customer-shared | docker login --username AWS --password-stdin $sharedaccountid.dkr.ecr.eu-west-1.amazonaws.com
echo
