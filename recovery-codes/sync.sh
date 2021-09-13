#!/usr/bin/env bash
set -euo pipefail

export AWS_PROFILE=irdn
aws sts get-caller-identity || aws sso login
BUCKET_NAME=$(aws ssm get-parameter --name=recovery-codes-bucket --query=Parameter.Value --with-decryption --output=text)
aws s3 sync . "s3://$BUCKET_NAME"
