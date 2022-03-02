#!/usr/bin/env bash
set -euxo pipefail

BROWSER=firefox
ACCOUNT_ID=$(aws sts get-caller-identity | jq -r ".Account")
aws-sso-util console launch -a $ACCOUNT_ID -r "AWSAdministratorAccess"
