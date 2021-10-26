import pytest
import boto3
from moto import mock_secretsmanager

from acme import acme


@mock_secretsmanager
def test_secrets_manager_client():
    conn = boto3.client("secretsmanager", region_name="us-east-1")
    conn.create_secret(Name="test/otter/credentials",
                       SecretString='{"username": "airbnb", "password": "test"}')
    output = acme.get_secret('test/otter/credentials', 'username', 'us-east-1')
    assert output == "airbnb"


@mock_secretsmanager
def test_invalid_secrets():
    conn = boto3.client("secretsmanager", region_name="us-east-1")
    conn.create_secret(Name="test/otter/account.json",
                       SecretString="secret")

    with pytest.raises(Exception) as error:
        acme.get_secret('test/otter/invalid.json', 'us-east-1')
    assert "ResourceNotFoundException" in str(error)


@mock_secretsmanager
def test_invalid_secrets_region():
    conn = boto3.client("secretsmanager", region_name="us-east-1")
    conn.create_secret(Name="test/otter/account.json",
                       SecretString="secret")

    with pytest.raises(Exception) as error:
        acme.get_secret('test/otter/invalid.json', 'us-west-1')
    assert "ResourceNotFoundException" in str(error)
