from moto import mock_dynamodb2

from config import (
    UNIT_TEST_NO_EXPIRATION_TOKEN,
    UNIT_TEST_NO_USERNAME_TOKEN,
    UNIT_TEST_EXPIRED_TOKEN,
    UNIT_TEST_INVALID_PRIVATE_KEY_TOKEN,
    ADMIN_TEST_ACCESS_TOKEN
)

def test_authentication_no_expiration(client):
    system_name = 'test.example.com'
    response = client.get(f'/api/v1/search?system_name=example.com', headers={"Authorization": f"Bearer {UNIT_TEST_NO_EXPIRATION_TOKEN}"})
    assert response.status_code == 401

def test_authentication_no_username(client):
    system_name = 'test.example.com'
    response = client.get(f'/api/v1/search?system_name=example.com', headers={"Authorization": f"Bearer {UNIT_TEST_NO_USERNAME_TOKEN}"})
    assert response.status_code == 401

def test_authentication_expired_token(client):
    system_name = 'test.example.com'
    response = client.get(f'/api/v1/search?system_name=example.com', headers={"Authorization": f"Bearer {UNIT_TEST_EXPIRED_TOKEN}"})
    assert response.status_code == 401

def test_authentication_no_bearer_header(client):
    response = client.get(f'/api/v1/search?system_name=example.com', headers={"Authorization": f"{ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 401

def test_authentication_no_header(client):
    system_name = 'test.example.com'
    response = client.get(f'/api/v1/search?system_name=example.com', headers={"Authorization": ""})
    assert response.status_code == 401

def test_authentication_invalid_private_key(client):
    system_name = 'test.example.com'
    response = client.get(f'/api/v1/search?system_name=example.com', headers={"Authorization": f"Bearer {UNIT_TEST_INVALID_PRIVATE_KEY_TOKEN}"})
    assert response.status_code == 401