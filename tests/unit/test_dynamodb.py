import pytest
import boto3
from moto.dynamodb2 import mock_dynamodb2

from otter.router.src.shared.client import DynamoDBClient, get_valid_devices
from otter.router.src.shared.device import Device

DYNAMODB_TABLE = "ottr-example"


@pytest.fixture
def _init_database():
    @mock_dynamodb2
    def dynamodb_client():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

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
            ]
        )

        # Populate Mock Database with Asset
        client = DynamoDBClient(region_name='us-east-1',
                                table_name=DYNAMODB_TABLE)
        device = Device(
            system_name='test.example.com',
            common_name='test.example.com',
            ip_address='10.0.0.1',
            certificate_authority='digicert',
            data_center='example',
            host_platform='panos',
            os_version='1.0.0',
            device_model='PA-XXXX',
            origin='API',
            subject_alternative_name=['example.com']
        )
        client.create_item(device)

        return dynamodb
    return dynamodb_client


@mock_dynamodb2
def test_dynamodb_update_item(_init_database, monkeypatch):
    monkeypatch.setenv('aws_region', 'us-east-1')
    monkeypatch.setenv('dynamodb_table', 'ottr-example')
    _init_database()

    client = DynamoDBClient(region_name='us-east-1', table_name=DYNAMODB_TABLE)
    device = Device(
        system_name='test.example.com',
        common_name='test.example.com',
        ip_address='10.0.0.1',
        certificate_authority='lets_encrypt',
        data_center='CHANGED',
        host_platform='panos',
        os_version='1.0.0',
        device_model='PA-XXXX',
        origin='API',
        subject_alternative_name=['example.com']
    )

    client.update_item(device)
    output = client._get_query('test.example.com')
    assert output['Items'][0].get('data_center') == 'CHANGED'


@mock_dynamodb2
def test_dynamodb_scan_table(_init_database, monkeypatch):
    monkeypatch.setenv('aws_region', 'us-east-1')
    monkeypatch.setenv('dynamodb_table', 'ottr-example')
    _init_database()

    client = DynamoDBClient(region_name='us-east-1', table_name=DYNAMODB_TABLE)
    output = client.scan_table()
    assert output.get('Count') == 1


@mock_dynamodb2
def test_dynamodb_put_multiple_items(_init_database, monkeypatch):
    monkeypatch.setenv('aws_region', 'us-east-1')
    monkeypatch.setenv('dynamodb_table', 'ottr-example')
    _init_database()

    client = DynamoDBClient(region_name='us-east-1', table_name=DYNAMODB_TABLE)
    device = Device(
        system_name='second.example.com',
        common_name='second.example.com',
        ip_address='10.0.0.1',
        certificate_authority='lets_encrypt',
        data_center='example',
        host_platform='panos',
        os_version='1.0.0',
        device_model='PA-XXXX',
        origin='API',
        subject_alternative_name=['example.com']
    )

    client.create_item(device)
    output = client.scan_table()
    assert output.get('Count') == 2


@mock_dynamodb2
def test_dynamodb_query_items_valid(_init_database, monkeypatch):
    monkeypatch.setenv('aws_region', 'us-east-1')
    monkeypatch.setenv('dynamodb_table', 'ottr-example')
    _init_database()

    client = DynamoDBClient(region_name='us-east-1', table_name=DYNAMODB_TABLE)
    device = Device(
        system_name='test.example.com',
        common_name='test.example.com',
        ip_address='10.0.0.1',
        certificate_authority='lets_encrypt',
        data_center='example',
        host_platform='panos',
        os_version='1.0.0',
        device_model='PA-XXXX',
        origin='API',
        subject_alternative_name=['example.com']
    )
    client.create_item(device)
    output = client._get_query('test.example.com')
    assert output['Items'][0].get('system_name') == 'test.example.com'


@mock_dynamodb2
def test_dynamodb_maintain_ca(_init_database, monkeypatch):
    monkeypatch.setenv('aws_region', 'us-east-1')
    monkeypatch.setenv('dynamodb_table', 'ottr-example')
    _init_database()

    client = DynamoDBClient(region_name='us-east-1', table_name=DYNAMODB_TABLE)
    device = Device(
        system_name='test.example.com',
        common_name='test.example.com',
        ip_address='10.0.0.1',
        certificate_authority='lets_encrypt',
        data_center='example',
        host_platform='panos',
        os_version='1.0.0',
        device_model='PA-XXXX',
        origin='API',
        subject_alternative_name=['example.com']
    )

    output = client.update_item(device)
    assert output['Attributes'].get('certificate_authority') == 'digicert'


@mock_dynamodb2
def test_dynamodb_delete_item(_init_database, monkeypatch):
    monkeypatch.setenv('aws_region', 'us-east-1')
    monkeypatch.setenv('dynamodb_table', 'ottr-example')
    _init_database()

    client = DynamoDBClient(region_name='us-east-1', table_name=DYNAMODB_TABLE)
    client.delete_item('test.example.com')

    output = client.scan_table()
    assert output.get('Count') == 0


@mock_dynamodb2
def test_dynamodb_expiration_lookup(_init_database, monkeypatch):
    monkeypatch.setenv('aws_region', 'us-east-1')
    monkeypatch.setenv('dynamodb_table', 'ottr-example')
    _init_database()

    client = DynamoDBClient(region_name='us-east-1', table_name=DYNAMODB_TABLE)
    assets = client.scan_table()

    output = get_valid_devices(assets, ['test.example.com'])
    assert output[0]['system_name'] == 'test.example.com'
