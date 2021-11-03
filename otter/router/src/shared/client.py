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
import time
import dateutil
from typing import List, Set, Union
from datetime import datetime, timedelta

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from .logger import get_logger  # pylint: disable=E0402
from .device import Device  # pylint: disable=E0402

LOGGER = get_logger(__name__)
CONF_ROUTE_FILE = os.path.join(
    os.path.dirname(__file__), '../config/route.json')


class DynamoDBClient:
    """Instantiate AWS DynamoDB Client"""

    def __init__(self, region_name, table_name) -> None:
        self._resource = boto3.resource(
            'dynamodb', region_name=region_name)
        self._table_name = table_name
        self._table = self._resource.Table(self._table_name)

    def _get_query(self, system_name: str) -> dict:
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

    def create_item(self, device: Device) -> Union[dict, None]:
        payload = {
            "system_name": device.system_name,
            "common_name": device.common_name,
            "ip_address": device.ip_address,
            "certificate_validation": "True",
            "host_platform": device.host_platform,
            "certificate_authority": device.certificate_authority,
            "os_version": device.os_version,
            "data_center": device.data_center,
            "device_model": device.device_model,
            "subject_alternative_name": device.subject_alternative_name,
            "origin": device.origin,
            "certificate_expiration": 'None'
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
                host_platform = :host_platform, os_version = :os_version, \
                data_center = :data_center, device_model = :device_model, \
                subject_alternative_name = :subject_alternative_name, origin = :origin, common_name = :common_name",
            ExpressionAttributeValues={
                ":ip_address": device.ip_address,
                ":common_name": device.common_name,
                ":host_platform": device.host_platform,
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


def lookup_attributes(device):
    task_definition = _validate_route(device)
    hosted_zone_id = _get_hosted_zone_id(device)
    if task_definition is not None:
        return task_definition, hosted_zone_id
    return None, None


def get_valid_devices(assets: dict, hosts: List) -> List:
    data = assets['Items']
    delta = 30
    rotate_assets = []

    for host in data:
        if host['system_name'] in hosts:
            if host['certificate_expiration'] == 'None':
                rotate_assets.append(host)
            else:
                rotation_date = (dateutil.parser.parse(
                    host['certificate_expiration']) - timedelta(days=delta)).isoformat()
                if datetime.utcnow().isoformat() > rotation_date:
                    rotate_assets.append(host)
    return rotate_assets


def start_execution(data):
    sfn_client = boto3.client('stepfunctions')
    output = sfn_client.start_execution(
        stateMachineArn=os.environ['step_function_arn'],
        name='otter_{0}'.format(time.time()),
        input=data
    )
    return output


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


def get_acme_challenge_records(hosted_zones: List[str]) -> Set[str]:
    """
    Gathers list of Hosted Zone IDs and query each zone to aggregate a list
    of devices that have a mapping from _acme-challenge.[FQDN]
    to_acme-challenge.[example-acme.com]. Without this mapping
    any certificate signing requests (CSR) that get sent to our
    certificateauthority (CA) will fail.

    Args:
        hosted_zones (List[str]): Gathers list of available Hosted
        Zone IDs from Route Table (route.json).

    Returns:
        Set: Unique list of hosts (FQDN) that have valid mappings to the subdelegate zone.
    """

    client = boto3.client('route53')
    paginator = client.get_paginator(
        'list_resource_record_sets')

    hosts = set()
    for zone in hosted_zones:
        try:
            records = paginator.paginate(
                HostedZoneId=zone)
            for record_set in records:
                for record in record_set['ResourceRecordSets']:
                    if record['Type'] == 'CNAME' and '_acme-challenge' in record['Name']:
                        hosts.add(record['Name'].split(
                            '.', 1)[1].rsplit('.', 1)[0])
        except Exception as error:
            LOGGER.error(error)
    return hosts
