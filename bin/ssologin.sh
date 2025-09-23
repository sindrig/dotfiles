#!/bin/bash
set -euxo pipefail

export BROWSER=firefox

customer=${1:-aftra}
case $customer in
    aftra)
        envs=('prod' 'dev' 'heimdallr' 'shared' 'build' 'sandbox')
        ;;
    *)
        echo "Unknown customer $customer"
	exit 1
        ;;
esac

i=$envs
uvx aws-sso-util login --profile $customer-${i}
if ! aws sts get-caller-identity --profile $customer-${i}; then
	rm -rf ~/.aws/sso/cache/*.json
	uvx aws-sso-util login --profile $customer-${i}
fi
envs=("${envs[@]:1}")

pids=()
for i in ${envs[*]}; do
    uvx aws-sso-util login --profile $customer-${i} &
    pids+=($!)
done

for pid in ${pids[*]}; do
    echo "Waiting for $pid"
    wait ${pid}
    echo "$pid done!"
done

echo "Finished all logins"
sharedaccountid=$(aws sts get-caller-identity --profile=$customer-shared --query=Account --output=text)
aws ecr get-login-password --profile=$customer-shared --region eu-west-1 | docker login --username AWS --password-stdin $sharedaccountid.dkr.ecr.eu-west-1.amazonaws.com
aws ecr get-login-password --profile=$customer-shared --region us-east-1 | docker login --username AWS --password-stdin $sharedaccountid.dkr.ecr.us-east-1.amazonaws.com
echo
