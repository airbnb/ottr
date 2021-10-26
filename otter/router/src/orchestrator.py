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

from shared.device import Device
from shared.logger import get_logger
from shared.client import start_execution, lookup_attributes, get_acme_challenge_records, get_valid_devices, DynamoDBClient

LOGGER = get_logger(__name__)
CONF_ROUTE_FILE = os.path.join(
    os.path.dirname(__file__), './config/route.json')


def main(event, lambda_context):
    """ Lambda function triggered from CloudWatch to update asset inventory
database as well as includes logic to trigger ECS Task for X.509 certificate
renewal depending on if platform is supported.

    Args:
        event ([type]): [description]
        lambda_context ([type]): [description]
    """

    dynamodb_client = DynamoDBClient(
        region_name=os.environ['aws_region'], table_name=os.environ['dynamodb_table'])

    # Pull Route53 Hosted Zone IDs
    with open(CONF_ROUTE_FILE, 'r') as file:
        metadata = json.load(file)
        hosted_zone_ids = list(metadata['hosted_zones'].values())

    # Populate Valid Network Devices
    available_records = get_acme_challenge_records(
        hosted_zone_ids)

    # Scan DDB for Hosts Set / Check Certificate Expiration
    assets = dynamodb_client.scan_table()
    rotate_assets = get_valid_devices(assets, available_records)
    LOGGER.info('Rotate Certificates: %s', str(rotate_assets))

    payload = {
        "assets": [],
        "region": os.environ['aws_region'],
        "table": os.environ['dynamodb_table']
    }

    for device in rotate_assets:
        task_definition, hosted_zone_id = lookup_attributes(device)
        if task_definition is not None:
            asset = {
                "hostname": device.get('system_name'),
                "common_name": device.get('common_name'),
                "certificate_validation": device.get('certificate_validation'),
                "task_definition": task_definition,
                "dns": hosted_zone_id
            }
            payload['assets'].append(asset)

    if payload['assets']:
        data = json.dumps(payload)
        start_execution(data)
