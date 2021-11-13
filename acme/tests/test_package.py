import os

import boto3
import requests
import pytest

from mock import patch
from moto import (
    mock_secretsmanager,
    mock_dynamodb2,
    mock_route53)

from acme import acme

DYNAMODB_TABLE = "ottr-example"
REGION = os.environ['AWS_REGION']

@mock_route53
def test_subject_alternative_names_validation(init_dns, secretsmanager_client):
    init_dns()

    subject_alternative_names = [
        'test.example.com']
    client = acme.LetsEncrypt(
        hostname='example.com', common_name='example.com', subdelegate='example-acme.com', subject_alternative_names=subject_alternative_names,
        region=REGION)


@mock_route53
def test_dns_acme_challenge_invalid(init_dns, secretsmanager_client):
    init_dns()

    subject_alternative_names = ['invalid.example.com']
    with pytest.raises(SystemExit) as system:
        client = acme.LetsEncrypt(
            hostname='example.com', common_name='example.com', subdelegate='example-acme.com', subject_alternative_names=subject_alternative_names,
            region=REGION)
        assert system.type == SystemExit
        assert system.value.code == 1

@mock_route53
@mock_secretsmanager
def test_register_lets_encrypt_account_exception(init_dns):
    init_dns()

    subject_alternative_names = ['test.example.com']
    with pytest.raises(SystemExit) as system:
        client = acme.LetsEncrypt(
            hostname='example.com', common_name='example.com', subdelegate='example-acme.com', subject_alternative_names=subject_alternative_names,
            region=REGION)
        assert system.type == SystemExit
        assert system.value.code == 1

@mock_dynamodb2
def test_query_subject_alternative_names(init_database):
    init_database()
    from boto3.dynamodb.conditions import Key
    hostname = 'example.com'
    region_name = os.environ['AWS_REGION']
    dynamodb_table = os.environ['DYNAMODB_TABLE']
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table(dynamodb_table)
    response = table.query(
        IndexName='system_name_index',
        KeyConditionExpression=Key('system_name').eq(hostname))
    query = acme.query_subject_alternative_names('example.com')
    assert query == ['dev.example.com']


@mock_dynamodb2
def test_update_certificate_expiration_format(init_database):
    init_database()
    certificate_expiration = '2021-01-01T00:00:00'
    response = acme.update_certificate_expiration(
        'example.com', certificate_expiration)
    assert response['Attributes']['certificate_expiration'] == '2021-01-01T00:00:00'


@mock_dynamodb2
@pytest.fixture
def test_update_certificate_invalid_expiration_format(init_database):
    init_database()
    certificate_expiration = '00:00:00'

    with pytest.raises(SystemExit) as system:
        acme.update_certificate_expiration(
            'example.com', certificate_expiration)
    assert system.type == SystemExit
    assert system.value.code == 1


@mock_dynamodb2
def test_openssl_certificate_check_remote(init_database):
    init_database()
    with pytest.raises(SystemExit) as system:
        output = acme.query_certificate_expiration(system_name='example.com', common_name='example.com')
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

class TestRequestPackage:
    test_cases = [('True'), ('False')]

    @pytest.mark.parametrize(('validation'), test_cases)
    def test_request_get(self, httpserver, validation):
        httpserver.expect_request("/get").respond_with_json({"foo": "bar"})
        url = httpserver.url_for("/get")
        acme_request = acme.Request(validation=validation)
        response = acme_request.get(url=url)
        assert response.status_code == 200

    @pytest.mark.parametrize(('validation'), test_cases)
    def test_request_post(self, httpserver, validation):
        httpserver.expect_request("/post").respond_with_json({"foo": "bar"})
        url = httpserver.url_for("/post")
        acme_request = acme.Request(validation=validation)
        response = acme_request.post(url=url)
        assert response.status_code == 200

    @pytest.mark.parametrize(('validation'), test_cases)
    def test_request_put(self, httpserver, validation):
        httpserver.expect_request("/put").respond_with_json({"foo": "bar"})
        url = httpserver.url_for("/put")
        acme_request = acme.Request(validation=validation)
        response = acme_request.put(url=url)
        assert response.status_code == 200

    @pytest.mark.parametrize(('validation'), test_cases)
    def test_request_delete(self, httpserver, validation):
        httpserver.expect_request("/delete").respond_with_json({"foo": "bar"})
        url = httpserver.url_for("/delete")
        acme_request = acme.Request(validation=validation)
        response = acme_request.delete(url=url)
        assert response.status_code == 200
