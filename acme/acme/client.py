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
import ssl
import sys
from datetime import datetime, timedelta
from typing import List, Tuple

import OpenSSL
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from .logger import get_logger

LOGGER = get_logger(__name__)

region_name = os.environ['AWS_REGION']
dynamodb_table = os.environ['DYNAMODB_TABLE']
dynamodb = boto3.resource('dynamodb', region_name=region_name)
table = dynamodb.Table(dynamodb_table)


def get_secret(path: str, element=None, region: str = 'us-east-1') -> str:
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


def query_subject_alternative_names(hostname: str) -> List[str]:
    response = table.query(
        IndexName='system_name_index',
        KeyConditionExpression=Key('system_name').eq(hostname))

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return response['Items'][0]['subject_alternative_name']
    else:
        LOGGER.error('DynamoDB Returned Invalid HTTPStatusCode')
        sys.exit(1)


def update_certificate_expiration(hostname: str, certificate_expiration: str) -> None:
    try:
        _ = datetime.fromisoformat(certificate_expiration)
        response = table.update_item(
            Key={
                'system_name': hostname
            },
            UpdateExpression="SET certificate_expiration = :certificate_expiration, certificate_validation = :certificate_validation",
            ExpressionAttributeValues={
                ":certificate_expiration": certificate_expiration,
                ":certificate_validation": "True"
            },
            ReturnValues="UPDATED_NEW"
        )
        LOGGER.info(response)
    except Exception as error:
        LOGGER.error(error)
        sys.exit(1)


def _query_primary_key(system_name: str) -> dict:
    response = table.query(
        IndexName='system_name_index',
        KeyConditionExpression=Key('system_name').eq(system_name))
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        LOGGER.error(response)
    return response


def _decode_certificate(certificate: str) -> Tuple[str, str]:
    x509 = OpenSSL.crypto.load_certificate(
        OpenSSL.crypto.FILETYPE_PEM, certificate)
    certificate_expiration = datetime.strptime(
        x509.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ').isoformat()
    certificate_issuer = x509.get_issuer().O
    return (certificate_expiration, certificate_issuer)


def query_certificate_expiration(system_name: str) -> str:
    excluded_platforms = ['Ubuntu', 'Windows']
    host_platform = _query_primary_key(
        system_name)['Items'][0].get('host_platform')
    certificate_authority = _query_primary_key(
        system_name)['Items'][0].get('certificate_authority')

    if host_platform in excluded_platforms:
        with open(
                '{directory}/.acme.sh/{hostname}/fullchain.cer'.format(directory=os.environ['HOME'], hostname=system_name), 'r') as file:
            certificate = file.read()
            certificate_expiration, certificate_issuer = _decode_certificate(
                certificate)
    else:
        certificate = ssl.get_server_certificate(
            ('{hostname}'.format(hostname=system_name), 443))
        certificate_expiration, certificate_issuer = _decode_certificate(
            certificate)

    ca_mapping = {
        'lets_encrypt': {
            'organization': ["Let's Encrypt", "(STAGING) Let's Encrypt"],
            'duration': 90
        },
        'digicert': {
            'organization': ["DigiCert Inc"],
            'duration': 397
        }
    }

    LOGGER.info(certificate_issuer)
    LOGGER.info(certificate_expiration)

    duration = ca_mapping[certificate_authority].get('duration') - 1
    certificate_duration_iso = (
        datetime.utcnow() + timedelta(days=duration)).isoformat()

    if certificate_expiration > certificate_duration_iso and certificate_issuer in ca_mapping[certificate_authority].get('organization'):
        return certificate_expiration
    else:
        LOGGER.error('Failure to Upload Certificate to Device')
        sys.exit(1)
