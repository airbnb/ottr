import os

import pytest
import boto3

from config import ADMIN_TEST_ACCESS_TOKEN, DEVELOPER_TEST_ACCESS_TOKEN

AWS_REGION = os.environ['AWS_DEFAULT_REGION']
def test_database_credentials(secretsmanager_client):
    from backend.app.shared.client import get_secret
    output = get_secret(path="test/otter/database", region=AWS_REGION)
    assert output == '{"POSTGRES_PASSWORD": "example"}'

def test_admin_v1_users_post(client):
    payload = {
        "username": "user",
        "password": "passw0rdVaL!d",
        "role": "DEVELOPER"
    }

    response = client.post('/admin/v1/users', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.json['username'] == 'user'

def test_admin_v1_users_post_user_exists(client):
    payload = {
        "username": "user",
        "password": "passw0rdVaL!d",
        "role": "DEVELOPER"
    }

    response = client.post('/admin/v1/users', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.json == {'Invalid Request': 'User Exists'}

def test_admin_v1_users_post_invalid_permission(client):
    payload = {
        "username": "user_01",
        "password": "passw0rdVaL!d",
        "role": "INVALID"
    }

    response = client.post('/admin/v1/users', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500

def test_admin_v1_users_post_invalid_credentials(client):
    payload = {
        "username": "user02",
        "password": "passw0rdVaL!d",
        "role": "DEVELOPER"
    }

    response = client.post('/admin/v1/users', json=payload, headers={"Authorization": f"Bearer {DEVELOPER_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500

def test_admin_v1_users_post_invalid_password(client):
    payload = {
        "username": "user02",
        "password": "password",
        "role": "DEVELOPER"
    }
    response = client.post('/admin/v1/users', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500

def test_admin_v1_users_get(client):
    response = client.get('/admin/v1/users', headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 200

def test_admin_v1_users_get_invalid_credentials(client):
    response = client.get('/admin/v1/users', headers={"Authorization": f"Bearer {DEVELOPER_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500

def test_admin_v1_users_delete(client):
    username='user'
    response = client.delete(f'/admin/v1/users/{username}', headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 204

def test_admin_v1_users_delete_not_present(client):
    username='InvalidUser'
    response = client.delete(f'/admin/v1/users/{username}', headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 204

def test_admin_v1_users_delete_invalid_credentials(client):
    username='InvalidUser'
    response = client.delete(f'/admin/v1/users/{username}', headers={"Authorization": f"Bearer {DEVELOPER_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500