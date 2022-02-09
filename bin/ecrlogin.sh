#!/usr/bin/env bash

ecr_region=${1:-eu-west-1}
accountid=$(aws sts get-caller-identity --query=Account --output=text)
aws ecr get-login-password | docker login --username AWS --password-stdin $accountid.dkr.ecr.$ecr_region.amazonaws.com
