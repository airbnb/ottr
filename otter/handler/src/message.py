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

import os
import json
import sys
import base64
import configparser

import requests
import boto3
from boto3.dynamodb.conditions import Key

from logger import get_logger  # pylint: disable=E0402

LOGGER = get_logger(__name__)


config = configparser.ConfigParser()
if not config.read('conf.ini'):
    LOGGER.error('Failed to Load conf.ini Configuration')
    sys.exit(1)

channel = config['Slack'].get('channel')
redirect = config['Slack'].get('redirect')


def _retrieve_secret(path, element=None):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=os.environ['aws_region']
    )
    response = client.get_secret_value(
        SecretId=path
    )
    if 'SecretString' in response:
        secret = response['SecretString']
        if element is None:
            return secret
        else:
            output = json.loads(secret)
            return output[element]
    else:
        decoded_binary_secret = base64.b64decode(
            response['SecretBinary'])


def _generate_payload(message, task_definition, task_id):
    with open('./payload.json') as file:
        region = os.environ['aws_region']
        data = json.load(file)
        data[0]['text']['text'] = message
        data[1]['elements'][0]['url'] = redirect
        data[1]['elements'][1][
            'url'] = f'https://console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:log-groups/log-group/$252Fecs$252Fotter/log-events/$252F{task_definition}$252Fotter$252F{task_id}'
        payload = json.dumps(data, indent=4)

    return payload


def _query_metadata(hostname: str):
    resource = boto3.resource(
        'dynamodb', region_name=os.environ['aws_region'])
    table = resource.Table(os.environ['dynamodb_table'])
    response = table.query(
        IndexName='system_name_index',
        KeyConditionExpression=Key('system_name').eq(hostname))
    return response


def post_message(hostname: str, task_definition: str, task_id: str) -> None:
    """ Sends message to Slack channel, used for alerting on errors. Output
        of Slack response will be logged to CloudWatch logs.

    Args:
        message (str): Message sent to Slack.
    """
    prefix = os.environ['prefix']
    oauth_token = _retrieve_secret(
        f'{prefix}/otter/slack')

    metadata = _query_metadata(hostname)
    output = metadata['Items'][0]
    fqdn = output.get('system_name')
    ip_address = output.get('ip_address')
    certificate_authority = output.get('certificate_authority')
    certificate_expiration = output.get('certificate_expiration')
    platform = output.get('host_platform')
    os_version = output.get('os_version')

    headers = {
        'post': {
            'Authorization': 'Bearer {}'.format(oauth_token),
            'Content-Type': 'application/json; charset=utf-8'
        },
        'get': {
            'Authorization': 'Bearer {}'.format(oauth_token),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    }
    message = (f'_Error Ocurred During Certificate Rotation_\n\n'
               f'*Hostname:* `{fqdn}`\n*IPv4 Address:* `{ip_address}`\n*Certificate Expiration:* `{certificate_expiration}`\n*Platform:* `{platform}`\n*OS Version:* `{os_version}`\n*Certificate Authority:* `{certificate_authority}`')

    payload = _generate_payload(message, task_definition, task_id)
    post_message_url = 'https://slack.com/api/chat.postMessage'
    post_data = {
        'token': oauth_token,
        'channel': channel,
        'blocks': payload
    }

    response = requests.post(
        post_message_url,
        headers=headers['post'],
        data=json.dumps(post_data)
    )

    LOGGER.info(response.text)
