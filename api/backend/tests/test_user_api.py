import pytest
import boto3
from moto import (
    mock_dynamodb2,
    mock_route53,
    mock_stepfunctions)

from config import (
    ADMIN_TEST_ACCESS_TOKEN)


def test_user_v1_authenticate_post(client):
    # Create User
    payload = {
        "username": "user",
        "password": "passw0rdVaL!d",
        "role": "DEVELOPER"
    }

    response = client.post('/admin/v1/users', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})

    # Authenticate
    payload = {
        "username": "user",
        "password": "passw0rdVaL!d",
    }
    response = client.post('/user/v1/authenticate', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 200

def test_user_v1_authenticate_post_invalid_user(client):
    # Authenticate
    payload = {
        "username": "user_invalid",
        "password": "invalid_Us3r!",
    }
    response = client.post('/user/v1/authenticate', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 401


def test_user_v1_authenticate_put(client):
    payload = {
        "username": "user",
        "password": "passw0rdVaL!d",
        "updated_password": "newPassw0rd!"
    }
    response = client.put('/user/v1/authenticate', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 204

def test_user_v1_authenticate_put_invalid_password(client):
    payload = {
        "username": "user",
        "password": "newPassw0rd!",
        "updated_password": "invalid"
    }
    response = client.put('/user/v1/authenticate', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500



