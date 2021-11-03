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
import os
import time
import re
from typing import Union

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from backend.app.shared.network import Device
from backend.app.shared.logger import get_logger

LOGGER = get_logger(__name__)

CONF_ROUTE_FILE = os.path.join(
    os.path.dirname(__file__), '../config/route.json')


def query_acme_challenge_records(domain: str, subdomain: str) -> bool:
    client = boto3.client('route53')
    paginator = client.get_paginator(
        'list_resource_record_sets')
    response = client.list_hosted_zones_by_name(
        DNSName=f'{domain}.',
        MaxItems='1'
    )
    hosted_zone_id = response['HostedZones'][0]['Id'].split('/')[-1]
    for page in paginator.paginate(HostedZoneId=hosted_zone_id):
        for record in page["ResourceRecordSets"]:
            if ('_acme-challenge.' + subdomain) in record['Name']:
                return True
    return False


def validate_password(password: str) -> bool:
    regex = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&.])[A-Za-z\d@$!#%*?&.]{8,}$"
    compile = re.compile(regex)
    search = re.search(compile, password)
    if search:
        return True
    else:
        return False


def _validate_route(host: dict) -> Union[str, None]:
    system_name = host.get('system_name')
    certificate_authority = host.get('certificate_authority')
    host_platform = host.get('host_platform')
    os_version = host.get('os_version')
    device_model = host.get('device_model')
    task_definition = None

    with open(CONF_ROUTE_FILE, 'r') as file:
        routes = json.load(file)

    try:
        if routes['platform'][host_platform]['os'][os_version]:
            # Check Optional Model Key
            if 'model' not in routes['platform'][host_platform]['os'][os_version]:
                task_definition = routes['platform'][host_platform]['os'][
                    os_version]['certificate_authority'][certificate_authority]
                return task_definition
            elif device_model in routes['platform'][host_platform]['os'][os_version]['model']:
                task_definition = routes['platform'][host_platform]['os'][
                    os_version]['certificate_authority'][certificate_authority]
                return task_definition
    except KeyError:
        LOGGER.error(
            f'Route Not Available for {system_name} [{host_platform} \
                {os_version} {certificate_authority}]')
    return None


def _get_hosted_zone_id(device: dict) -> str:
    system_name = device.get('system_name')
    domain = '.'.join(system_name.split('.')[-2:])
    with open(CONF_ROUTE_FILE, 'r') as file:
        metadata = json.load(file)
        return metadata['hosted_zones'].get(domain)


def start_execution(device):
    task_definition = _validate_route(device)
    hosted_zone_id = _get_hosted_zone_id(device)
    system_name = device.get('system_name')
    common_name = device.get('common_name')
    certificate_validation = device.get('certificate_validation')
    region = os.environ['AWS_DEFAULT_REGION']
    account = os.environ['AWS_ACCOUNT']
    table = os.environ['TABLE']
    step_function_arn = f'arn:aws:states:{region}:{account}:stateMachine:otter-state'
    payload = {
        "assets": [
            {
                "hostname": system_name,
                "common_name": common_name,
                "certificate_validation": certificate_validation,
                "task_definition": task_definition,
                "dns": hosted_zone_id
            }
        ],
        "region": region,
        "table": table
    }
    if task_definition is not None:
        data = json.dumps(payload)
        sfn_client = boto3.client('stepfunctions')
        output = sfn_client.start_execution(
            stateMachineArn=step_function_arn,
            name='otter_{0}'.format(time.time()),
            input=data
        )
        return output
    else:
        return None


def get_secret(path, element=None, region: str = 'us-east-1') -> str:
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=path
        )
    except ClientError as error:
        raise error
    else:
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            if element is None:
                return secret
            else:
                output = json.loads(secret)
                return output[element]


class DynamoDBClient:
    """Instantiate AWS DynamoDB Client"""

    def __init__(self, region_name, table_name) -> None:
        self._resource = boto3.resource(
            'dynamodb', region_name=region_name)
        self._table_name = table_name
        self._table = self._resource.Table(self._table_name)

    def query_primary_key(self, system_name: str) -> dict:
        """
        Query DynamoDB asset inventory database based on primary sort key
        (system_name) which is the fully qualified domain name (FQDN) of a
        device.

        Args:
            system_name (str): Fully Qualified Domain Name (FQDN) i.e. test.example.com

        Returns:
            dict: AWS DynamoDB Query Response
        """
        response = self._table.query(
            IndexName='system_name_index',
            KeyConditionExpression=Key('system_name').eq(system_name))
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            LOGGER.error(response)
        return response

    def query_index(self, index_name, partition_key, value):
        response = self._table.query(
            IndexName=index_name,
            KeyConditionExpression=Key(partition_key).eq(value))
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            LOGGER.error(response)
        return response

    def create_item(self, device: Device) -> Union[dict, None]:
        payload = {
            "system_name": device.system_name,
            'common_name': device.common_name,
            "ip_address": device.ip_address,
            "host_platform": device.host_platform,
            "certificate_authority": device.certificate_authority,
            "os_version": device.os_version,
            "data_center": device.data_center,
            "device_model": device.device_model,
            "subject_alternative_name": device.subject_alternative_name,
            "origin": device.origin,
            "certificate_expiration": 'None',
            "certificate_validation": 'True'
        }
        response = self._table.put_item(Item=payload)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            LOGGER.info(f'New Item Created in DynamoDB: {payload}')
        else:
            LOGGER.error(f'Error ({device.system_name}): {response}')
        return response

    def update_item(self, device: Device) -> Union[dict, None]:
        response = self._table.update_item(
            Key={
                'system_name': device.system_name
            },
            UpdateExpression="SET ip_address = :ip_address, \
                host_platform = :host_platform, common_name = :common_name, \
                origin = :origin, os_version = :os_version, \
                data_center = :data_center, device_model = :device_model, \
                subject_alternative_name = :subject_alternative_name",
            ExpressionAttributeValues={
                ":ip_address": device.ip_address,
                ":host_platform": device.host_platform,
                ":common_name": device.common_name,
                ":os_version": device.os_version,
                ":data_center": device.data_center,
                ":device_model": device.device_model,
                ":subject_alternative_name": device.subject_alternative_name,
                ":origin": device.origin
            },
            ReturnValues="ALL_NEW"
        )
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            LOGGER.error(f'Error ({device.system_name}): {response}')
        return response

    def set_certificate_validation(self, system_name: str, status: str) -> Union[dict, None]:
        response = self._table.update_item(
            Key={
                'system_name': system_name
            },
            UpdateExpression="SET certificate_validation = :certificate_validation",
            ExpressionAttributeValues={
                ":certificate_validation": status,
            },
            ReturnValues="ALL_NEW"
        )
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            LOGGER.error(f'Error ({system_name}): {response}')
        return response

    def scan_table(self) -> dict:
        """
        Scan elements of asset inventory database within DynamoDB.

        Returns:
            [dict]: AWS DynamoDB scan() Response
        """
        response = self._table.scan()
        LOGGER.info(f'Scanned Table: {response}')
        return response

    def delete_item(self, system_name: str) -> dict:
        """
        Delete element within asset inventory database in DynamoDB.

        Args:
            system_name (str): Fully Qualified Domain Name (FQDN)
            of device to be deleted.

        Returns:
            dict: AWS DynamoDB delete_item() Response
        """
        response = self._table.delete_item(
            TableName=self._table_name,
            Key={
                "system_name": system_name
            },
            ConditionExpression="attribute_exists (system_name)",
        )
        LOGGER.info(f'Deleted {system_name} from DynamoDB: {response}')
        return response
