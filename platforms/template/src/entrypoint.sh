#!/bin/sh

export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/otter-server-ecs-fargate"

export AWS_STS_ASSUME_ROLE_OUTPUT="$(aws sts assume-role --role-arn $ROLE_ARN --role-session-name otter)"

export AWS_ACCESS_KEY_ID="$(echo $AWS_STS_ASSUME_ROLE_OUTPUT | jq '.Credentials.AccessKeyId' -r)"
export AWS_SECRET_ACCESS_KEY="$(echo $AWS_STS_ASSUME_ROLE_OUTPUT | jq '.Credentials.SecretAccessKey' -r)"
export AWS_SESSION_TOKEN="$(echo $AWS_STS_ASSUME_ROLE_OUTPUT | jq '.Credentials.SessionToken' -r)"

# Application Entrypoint
./app.py
