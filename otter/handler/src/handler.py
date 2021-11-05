"""
Copyright 2021-present Airbnb, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json

from logger import get_logger
from message import post_message, post_error_message

LOGGER = get_logger(__name__)


def main(event, lambda_context):
    LOGGER.info(event)
    error = event['Input']['Error']
    if error == 'States.TaskFailed':
        cause = event['Input']['Cause']
        output = json.loads(cause)
        task_arn = output['Containers'][0]['TaskArn']
        task_id = task_arn.split('/')[-1]
        task_definition = output['Group'].split(':')[-1]
        environment = output['Overrides']['ContainerOverrides'][0]['Environment']

        sent_message = False
        for elem in environment:
            if elem['Name'] == 'SYSTEM_NAME':
                hostname = elem['Value']
                post_message(hostname=hostname,
                             task_definition=task_definition, task_id=task_id)
                sent_message = True
                break
        if sent_message is False:
            message = (
                f'_Error Ocurred in Lambda Handler for `{hostname}` Container Runtime, Please Investigate CloudWatch Logs._')
            post_error_message(message)
    else:
        # ECS.ClientException
        message = (
            f'_`{error}` Error Ocurred in Lambda Handler during Container Runtime, Please Investigate CloudWatch Logs._')
        post_error_message(message)
