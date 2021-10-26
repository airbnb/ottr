import os

import boto3
import requests
import pytest

from mock import patch, Mock
from moto.route53 import mock_route53
from moto import mock_secretsmanager
from moto.dynamodb2 import mock_dynamodb2

from otter.router.src.shared.device import Device
from otter.router.src.shared.client import DynamoDBClient

from acme import acme

DYNAMODB_TABLE = "otter-example"
REGION = os.environ['AWS_REGION']

@pytest.fixture
def _init_dns():
    @mock_route53
    def route53_client():
        conn = boto3.client("route53", region_name=REGION)
        # Subdelegate Zone
        conn.create_hosted_zone(
            Name="example-acme.com.",
            CallerReference=str(hash("foo")),
            HostedZoneConfig=dict(
                PrivateZone=True, Comment="Subdelegate Zone"),
        )

        # Main Hosted Zone
        conn.create_hosted_zone(
            Name="example.com.",
            CallerReference=str(hash("bar")),
            HostedZoneConfig=dict(
                PrivateZone=True, Comment="Subdelegate Zone"),
        )

        # example.com Route53 Hosted Zone ID
        hosted_zone_id = conn.list_hosted_zones_by_name(
            DNSName="example.com.").get('HostedZones')[0].get('Id').split('/')[-1]

        # Create CNAME Mapping _acme-challenge.subdomain.example.com =>
        # _acme-challenge.example-acme.com
        cname_record_endpoint_payload = {
            "Comment": "Create CNAME record _acme-challenge.airbnb.example.com",
            "Changes": [
                {
                    "Action": "CREATE",
                    "ResourceRecordSet": {
                        "Name": "_acme-challenge.subdomain.example.com.",
                        "Type": "CNAME",
                        "TTL": 10,
                        "ResourceRecords": [{"Value": "_acme-challenge.example-acme.com."}],
                    },
                }
            ],
        }

        conn.change_resource_record_sets(
            HostedZoneId=hosted_zone_id, ChangeBatch=cname_record_endpoint_payload
        )

        # Create CNAME Mapping _acme-challenge.secondary.example.com =>
        # _acme-challenge.example-acme.com
        cname_record_endpoint_payload = {
            "Comment": "Create CNAME record _acme-challenge.secondary.example.com",
            "Changes": [
                {
                    "Action": "CREATE",
                    "ResourceRecordSet": {
                        "Name": "_acme-challenge.secondary.example.com.",
                        "Type": "CNAME",
                        "TTL": 10,
                        "ResourceRecords": [{"Value": "_acme-challenge.example-acme.com."}],
                    },
                }
            ],
        }

        conn.change_resource_record_sets(
            HostedZoneId=hosted_zone_id, ChangeBatch=cname_record_endpoint_payload
        )
        return hosted_zone_id
    return route53_client


@pytest.fixture
def _init_database():
    @mock_dynamodb2
    def dynamodb_client():
        dynamodb = boto3.resource('dynamodb', region_name=REGION)

        # Create Mock DynamoDB Database
        dynamodb.create_table(
            TableName=DYNAMODB_TABLE,
            KeySchema=[
                {"AttributeName": "system_name", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "system_name", "AttributeType": "S"},
                {"AttributeName": "ip_address", "AttributeType": "S"},
                {"AttributeName": "data_center", "AttributeType": "S"},
                {"AttributeName": "host_platform", "AttributeType": "S"},
                {"AttributeName": "origin", "AttributeType": "S"}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'system_name_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'system_name',
                            'KeyType': 'HASH'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    },
                },
                {
                    'IndexName': 'host_platform_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'host_platform',
                            'KeyType': 'HASH'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    },
                },
                {
                    'IndexName': 'ip_address_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'ip_address',
                            'KeyType': 'HASH'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    },
                },
                {
                    'IndexName': 'data_center_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'data_center',
                            'KeyType': 'HASH'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    },
                },
                {
                    'IndexName': 'origin_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'origin',
                            'KeyType': 'HASH'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    },
                },
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 10, "WriteCapacityUnits": 10},
        )

        # Populate Mock Database with Asset
        client = DynamoDBClient(region_name=REGION,
                                table_name=DYNAMODB_TABLE)

        device = Device(
            system_name='example.com',
            ip_address='10.0.0.1',
            certificate_authority='digicert',
            data_center='example',
            host_platform='panos',
            os_version='1.0.0',
            device_model='PA-XXXX',
            origin='API',
            subject_alternative_name=[
                'subdomain.example.com', 'secondary.example.com']
        )
        client.put_item(device)
        acme.update_certificate_expiration(
            'example.com', '2021-10-31T01:49:35')

        return dynamodb
    return dynamodb_client


@mock_route53
@mock_secretsmanager
def test_subject_alternative_names_validation(_init_dns, monkeypatch):
    monkeypatch.setenv('PREFIX', 'test')
    monkeypatch.setenv('AWS_REGION', REGION)

    conn = boto3.client("secretsmanager", region_name=REGION)
    conn.create_secret(Name="test/otter/account.json",
                       SecretString="secret")
    conn.create_secret(Name="test/otter/account.key", SecretString="secret")
    conn.create_secret(Name="test/otter/ca.conf", SecretString="secret")

    hosted_zone_id = _init_dns()
    monkeypatch.setenv('HOSTED_ZONE_ID', hosted_zone_id)

    subject_alternative_names = [
        'subdomain.example.com', 'secondary.example.com']
    client = acme.LetsEncrypt(
        hostname='example.com', subdelegate='example-acme.com', subject_alternative_names=subject_alternative_names,
        region=REGION)


@mock_route53
@mock_secretsmanager
def test_dns_acme_challenge_invalid(_init_dns, monkeypatch):
    monkeypatch.setenv('PREFIX', 'test')
    monkeypatch.setenv('AWS_REGION', REGION)

    conn = boto3.client("secretsmanager", region_name=REGION)
    conn.create_secret(Name="test/otter/account.json",
                       SecretString="secret")
    conn.create_secret(Name="test/otter/account.key", SecretString="secret")
    conn.create_secret(Name="test/otter/ca.conf", SecretString="secret")

    hosted_zone_id = _init_dns()
    monkeypatch.setenv('HOSTED_ZONE_ID', hosted_zone_id)

    subject_alternative_names = ['invalid.example.com']
    with pytest.raises(SystemExit) as system:
        client = acme.LetsEncrypt(
            hostname='example.com', subdelegate='example-acme.com', subject_alternative_names=subject_alternative_names,
            region=REGION)
        assert system.type == SystemExit
        assert system.value.code == 1


@mock_route53
def test_register_lets_encrypt_account_exception(_init_dns, monkeypatch):
    monkeypatch.setenv('PREFIX', 'test')
    monkeypatch.setenv('AWS_REGION', REGION)

    hosted_zone_id = _init_dns()
    monkeypatch.setenv('HOSTED_ZONE_ID', hosted_zone_id)

    subject_alternative_names = ['subdomain.example.com']
    with pytest.raises(SystemExit) as system:
        client = acme.LetsEncrypt(
            hostname='example.com', subdelegate='example-acme.com', subject_alternative_names=subject_alternative_names,
            region=REGION)
        assert system.type == SystemExit
        assert system.value.code == 1


@mock_route53
@mock_secretsmanager
def test_register_lets_encrypt_account(_init_dns, monkeypatch):
    monkeypatch.setenv('PREFIX', 'test')
    monkeypatch.setenv('AWS_REGION', REGION)

    hosted_zone_id = _init_dns()
    monkeypatch.setenv('HOSTED_ZONE_ID', hosted_zone_id)

    conn = boto3.client("secretsmanager", region_name=REGION)
    conn.create_secret(Name="test/otter/account.json",
                       SecretString="secret")
    conn.create_secret(Name="test/otter/account.key", SecretString="secret")
    conn.create_secret(Name="test/otter/ca.conf", SecretString="secret")

    subject_alternative_names = ['subdomain.example.com']
    client = acme.LetsEncrypt(
        hostname='example.com', subdelegate='example-acme.com', subject_alternative_names=subject_alternative_names,
        region=REGION)


@mock_route53
@mock_secretsmanager
def test_hosted_zone_id_exception(_init_dns, monkeypatch):
    monkeypatch.setenv('PREFIX', 'test')
    monkeypatch.setenv('AWS_REGION', REGION)
    _init_dns()

    conn = boto3.client("secretsmanager", region_name=REGION)
    conn.create_secret(Name="test/otter/account.json",
                       SecretString="secret")
    conn.create_secret(Name="test/otter/account.key", SecretString="secret")
    conn.create_secret(Name="test/otter/ca.conf", SecretString="secret")

    subject_alternative_names = ['invalid.example.com']
    with pytest.raises(SystemExit):
        client = acme.LetsEncrypt(
            hostname='example.com', subdelegate='example-acme.com', subject_alternative_names=subject_alternative_names,
            region=REGION)


@mock_dynamodb2
def test_query_subject_alternative_names(_init_database, monkeypatch):
    monkeypatch.setenv('aws_region', REGION)

    _init_database()
    query = acme.query_subject_alternative_names('example.com')
    assert query == ['subdomain.example.com', 'secondary.example.com']


@mock_dynamodb2
def test_update_certificate_expiration_format(_init_database, monkeypatch):
    monkeypatch.setenv('aws_region', REGION)

    _init_database()
    certificate_expiration = '2021-01-01T00:00:00'
    acme.update_certificate_expiration(
        'example.com', certificate_expiration)


@mock_dynamodb2
def test_update_certificate_invalid_expiration_format(_init_database, monkeypatch):
    monkeypatch.setenv('aws_region', REGION)

    _init_database()
    certificate_expiration = '00:00:00'

    with pytest.raises(SystemExit) as system:
        acme.update_certificate_expiration(
            'example.com', certificate_expiration)
    assert system.type == SystemExit
    assert system.value.code == 1


@mock_dynamodb2
def test_openssl_certificate_check(_init_database):
    _init_database()
    with pytest.raises(SystemExit) as system:
        acme.query_certificate_expiration('example.com')
        assert system.type == SystemExit
        assert system.value.code == 1

def test_http_generic_exception():
    @patch('requests.post')
    @acme.generic_exception(message='Error')
    def test_generic(post_mock):
        post_mock.side_effect = ValueError()
        return post_mock.side_effect

    with pytest.raises(ValueError):
        test_generic()


@patch('requests.head')
def test_connection_error(mock):
    with pytest.raises(Exception):
        mock.side_effect = requests.exceptions.ConnectionError()
        acme.LetsEncrypt._validate_device_connection(
            hostname='https://example.com')


@patch('requests.head')
def test_connection_error(mock):
    with pytest.raises(Exception):
        mock.side_effect = requests.exceptions.ConnectionError()
        acme.LetsEncrypt._validate_device_connection(
            hostname='invalid-domain-example-test.com')
