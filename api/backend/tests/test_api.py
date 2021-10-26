import pytest
import boto3
from moto import (
    mock_dynamodb2,
    mock_route53,
    mock_stepfunctions)

from config import ADMIN_TEST_ACCESS_TOKEN

@mock_dynamodb2
def test_api_v1_assets_post_valid(init_database, client):
    init_database()
    payload = {
        "system_name": "subdomain.example.com",
        "common_name": "subdomain.example.com",
        "certificate_authority": "lets_encrypt",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.1",
        "os_version": "9.1.0",
        "subject_alternative_name": [
            "test.example.com"
        ]
    }

    response = client.post('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.json['system_name'] == 'subdomain.example.com'

def test_api_v1_assets_post_invalid_ip_address(client):
    payload = {
        "system_name": "subdomain.example.com",
        "common_name": "subdomain.example.com",
        "certificate_authority": "lets_encrypt",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "INVALID",
        "os_version": "9.1.0",
        "subject_alternative_name": [
            "test.example.com"
        ]
    }
    response = client.post('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.json['status'] == 'ip_address Does Not Contain Valid IPv4 Address: INVALID'

def test_api_v1_assets_post_invalid_ip_address_integer(client):
    payload = {
        "system_name": "subdomain.example.com",
        "common_name": "subdomain.example.com",
        "certificate_authority": "lets_encrypt",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.300",
        "os_version": "9.1.0",
        "subject_alternative_name": [
            "test.example.com"
        ]
    }
    response = client.post('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500

def test_api_v1_assets_post_invalid_ip_address_octet(client):
    payload = {
        "system_name": "subdomain.example.com",
        "common_name": "subdomain.example.com",
        "certificate_authority": "lets_encrypt",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.A",
        "os_version": "9.1.0",
        "subject_alternative_name": [
            "test.example.com"
        ]
    }
    response = client.post('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500

def test_api_v1_assets_post_invalid_system_name(client):
    payload = {
        "system_name": "INVALID",
        "common_name": "subdomain.example.com",
        "certificate_authority": "lets_encrypt",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.1",
        "os_version": "9.1.0",
        "subject_alternative_name": [
            "test.example.com"
        ]
    }
    response = client.post('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.json['status'] == 'system_name Does Not Contain a FQDN: INVALID'

def test_api_v1_assets_post_invalid_system_name_domain(client):
    payload = {
        "system_name": "test.sample.com",
        "common_name": "subdomain.example.com",
        "certificate_authority": "lets_encrypt",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.1",
        "os_version": "9.1.0",
        "subject_alternative_name": [
            "test.example.com"
        ]
    }
    response = client.post('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500

def test_api_v1_assets_post_invalid_certificate_authority(client):
    payload = {
        "system_name": "test.example.com",
        "common_name": "subdomain.example.com",
        "certificate_authority": "INVALID",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.1",
        "os_version": "9.1.0",
        "subject_alternative_name": [
            "test.example.com"
        ]
    }
    response = client.post('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500

def test_api_v1_assets_post_invalid_host_platform(client):
    payload = {
        "system_name": "test.example.com",
        "common_name": "subdomain.example.com",
        "certificate_authority": "lets_encrypt",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "INVALID",
        "ip_address": "10.0.0.1",
        "os_version": "9.1.0",
        "subject_alternative_name": [
            "test.example.com"
        ]
    }
    response = client.post('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500

def test_api_v1_assets_post_invalid_common_name_domain(client):
    payload = {
        "system_name": "test.example.com",
        "common_name": "test.sample.com",
        "certificate_authority": "lets_encrypt",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.1",
        "os_version": "9.1.0",
        "subject_alternative_name": [
            "test.example.com"
        ]
    }
    response = client.post('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500

def test_api_v1_assets_post_invalid_common_name(client):
    payload = {
        "system_name": "test.example.com",
        "common_name": "INVALID",
        "certificate_authority": "lets_encrypt",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.1",
        "os_version": "9.1.0",
        "subject_alternative_name": [
            "test.example.com"
        ]
    }
    response = client.post('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500

def test_api_v1_assets_post_invalid_subject_alternative_name_domain(client):
    payload = {
        "system_name": "test.example.com",
        "common_name": "subdomain.example.com",
        "certificate_authority": "lets_encrypt",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.1",
        "os_version": "9.1.0",
        "subject_alternative_name": [
            "test.sample.com"
        ]
    }
    response = client.post('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500

def test_api_v1_assets_post_invalid_subject_alternative_name_wildcard(client):
    payload = {
        "system_name": "test.example.com",
        "common_name": "subdomain.example.com",
        "certificate_authority": "lets_encrypt",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.1",
        "os_version": "9.1.0",
        "subject_alternative_name": [
            "*"
        ]
    }
    response = client.post('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500

@mock_dynamodb2
def test_api_v1_assets_post_device_exists(init_database, client):
    init_database()
    payload = {
        "system_name": "test.example.com",
        "common_name": "subdomain.example.com",
        "certificate_authority": "lets_encrypt",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.1",
        "os_version": "9.1.0",
        "subject_alternative_name": []
    }
    response = client.post('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 500

@mock_dynamodb2
def test_api_v1_assets_post_empty_sans(init_database, client):
    init_database()
    payload = {
        "system_name": "subdomain.example.com",
        "common_name": "sample.example.com",
        "certificate_authority": "lets_encrypt",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.1",
        "os_version": "9.1.0",
        "subject_alternative_name": []
    }
    response = client.post('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.json

@mock_dynamodb2
def test_api_v1_assets_put(init_database, client):
    init_database()
    payload = {
        "system_name": "test.example.com",
        "common_name": "test.example.com",
        "certificate_authority": "lets_encrypt",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.2",
        "os_version": "9.1.0",
        "subject_alternative_name": []
    }
    response = client.put('/api/v1/assets', json=payload, headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.json['ip_address'] == '10.0.0.2'

@mock_dynamodb2
def test_api_v1_assets_delete(init_database, client):
    init_database()
    system_name = 'test.example.com'
    response = client.delete(f'/api/v1/assets/delete/{system_name}', headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 204

@mock_dynamodb2
def test_api_v1_assets_delete_invalid_host(init_database, client):
    init_database()
    system_name = 'subdomain.example.com'
    response = client.delete(f'/api/v1/assets/delete/{system_name}', headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 200

@mock_dynamodb2
def test_api_v1_search_system_name(init_database, client):
    init_database()
    system_name = 'test.example.com'
    response = client.get(f'/api/v1/search?system_name={system_name}', headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 200

@mock_dynamodb2
def test_api_v1_search_system_name(init_database, client):
    init_database()
    ip_address = '10.0.0.1'
    response = client.get(f'/api/v1/search?ip_address={ip_address}', headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 200

@mock_dynamodb2
def test_api_v1_search_days_until_expiration(init_database, client):
    init_database()
    expiration = '30'
    response = client.get(f'/api/v1/search?days_until_expiration={expiration}', headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 200

@mock_route53
@mock_stepfunctions
@mock_dynamodb2
def test_api_v1_certificate_rotate(init_dns, init_database, init_state, client):
    init_dns()
    init_database()
    init_state()
    system_name = 'test.example.com'
    response = client.post(f'/api/v1/certificate/rotate/{system_name}', headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 204

@mock_route53
@mock_stepfunctions
@mock_dynamodb2
def test_api_v1_certificate_rotate_invalid_dns_record(init_dns, init_database, init_state, client):
    init_dns()
    init_database()
    init_state()
    system_name = 'ubuntu.example.com'
    response = client.post(f'/api/v1/certificate/rotate/{system_name}', headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 200

@mock_dynamodb2
def test_api_v1_management_certificate_validation_set_patch(init_database, client):
    init_database()
    system_name = 'ubuntu.example.com'
    response = client.patch(f'/api/v1/management/certificate-validation/set/{system_name}', headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 200

@mock_dynamodb2
def test_api_v1_management_certificate_validation_unset_patch(init_database, client):
    init_database()
    system_name = 'ubuntu.example.com'
    response = client.patch(f'/api/v1/management/certificate-validation/unset/{system_name}', headers={"Authorization": f"Bearer {ADMIN_TEST_ACCESS_TOKEN}"})
    assert response.status_code == 200
