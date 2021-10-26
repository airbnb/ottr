import pytest
import boto3
from moto import mock_secretsmanager

from otter.router.src.shared.client import get_secret


@mock_secretsmanager
def test_secrets_manager_key():
    conn = boto3.client("secretsmanager", region_name="us-east-1")
    conn.create_secret(Name="test/otter/credentials",
                       SecretString='{"username": "airbnb", "password": "test"}')
    output = get_secret('test/otter/credentials', 'username', 'us-east-1')
    assert output == "airbnb"


@mock_secretsmanager
def test_secrets_manager_plaintext():
    conn = boto3.client("secretsmanager", region_name="us-east-1")
    conn.create_secret(Name="test/otter/account.json",
                       SecretString="secret")

    output = get_secret('test/otter/account.json', region='us-east-1')
    assert output == "secret"
@mock_secretsmanager
def test_invalid_secrets():
    conn = boto3.client("secretsmanager", region_name="us-east-1")
    conn.create_secret(Name="test/otter/account.json",
                       SecretString="secret")

    with pytest.raises(Exception) as error:
        get_secret('test/otter/invalid.json', region='us-east-1')
    assert "ResourceNotFoundException" in str(error)


@mock_secretsmanager
def test_invalid_secrets_region():
    conn = boto3.client("secretsmanager", region_name="us-east-1")
    conn.create_secret(Name="test/otter/account.json",
                       SecretString="secret")

    with pytest.raises(Exception) as error:
        get_secret('test/otter/invalid.json', region='us-west-1')
    assert "ResourceNotFoundException" in str(error)
