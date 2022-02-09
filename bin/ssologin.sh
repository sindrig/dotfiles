#!/bin/bash
set -euo pipefail

export BROWSER=firefox

customer=${1:-syndis}
ecr_region=eu-west-1
case $customer in
    syndis)
        envs=('prod' 'dev' 'shared')
        ;;
    *)
        echo "Unknown customer $customer"
	exit 1
        ;;
esac

i=$envs
aws-sso-util login --profile $customer-${i}
if ! aws sts get-caller-identity --profile $customer-${i}; then
	rm -rf ~/.aws/sso/cache/*.json
	aws-sso-util login --profile $customer-${i}
fi
envs=("${envs[@]:1}")

pids=()
for i in ${envs[*]}; do
    aws-sso-util login --profile $customer-${i} &
    pids+=($!)
done

for pid in ${pids[*]}; do
    echo "Waiting for $pid"
    wait ${pid}
    echo "$pid done!"
done

echo "Finished all logins"
sharedaccountid=$(aws sts get-caller-identity --profile=$customer-shared --query=Account --output=text)
aws ecr get-login-password --profile=$customer-shared | docker login --username AWS --password-stdin $sharedaccountid.dkr.ecr.$ecr_region.amazonaws.com
echo
