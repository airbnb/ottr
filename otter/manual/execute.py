import time
import json

import boto3

REGION = ''
AWS_ACCOUNT = ''
DYNAMODB_TABLE = ''

STEP_FUNCTION_ARN = f'arn:aws:states:{REGION}:{AWS_ACCOUNT}:stateMachine:otter-state'

# Example Payload
payload = {
    "assets": [
        {
            "hostname": "panos01.example.com",
            "common_name": "panos01.example.com",
            "certificate_validation": "True",
            "task_definition": "otter-panos-9x-lets-encrypt",
            "dns": "xxx (Route53 Hosted Zone ID)"
        },
        {
            "hostname": "f501.example.com",
            "common_name": "f501.example.com",
            "certificate_validation": "False",
            "task_definition": "otter-f5-14x-lets-encrypt",
            "dns": "xxx (Route53 Hosted Zone ID)"
        }
    ],
    "region": REGION,
    "table": DYNAMODB_TABLE
}
string_payload = json.dumps(payload)

if __name__ == "__main__":
    sfn_client = boto3.client('stepfunctions')
    output = sfn_client.start_execution(
        stateMachineArn=STEP_FUNCTION_ARN,
        name='otter_{0}'.format(time.time()),
        input=string_payload
    )
