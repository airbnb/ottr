#!/usr/local/bin/python

import os
import sys
import requests
import json
import time

import acme

LOGGER = acme.get_logger(__name__)


def generate_api_token(hostname, username, password):
    url = 'https://{hostname}/api/v3.7/sessions'.format(hostname=hostname)
    data = {
        "username": username,
        "password": password
    }
    response = acme_request.post(url, data=json.dumps(data))
    output = response.json()
    return output['session']


def generate_csr(hostname, common_name, session):
    url = 'https://{hostname}/api/v3.7/services/https'.format(
        hostname=hostname)
    data = {
        'https': {
            'common_name': common_name,
            'organization': os.environ['organization'],
            'key_length': 2048,
            'csr': {
                'csr': 'new',
                'country': os.environ['country'],
                'state': os.environ['state'],
                'locality': os.environ['locality'],
                'common_name': common_name,
                'email': os.environ['email'],
                'key_length': 2048,
                'organization': os.environ['organization'],
                'org_unit': os.environ['organization_unit']
            }
        }
    }
    headers = {'Authorization': 'Token {session}'.format(session=session)}
    response = acme_request.put(url, headers=headers, data=json.dumps(data))
    path = os.environ['HOME']
    output = json.loads(response.text)
    url = output['https']['csr']['csr']
    csr_path = "{path}/output.csr".format(path=path)
    response = acme_request.get(url, headers=headers)
    open(csr_path, 'wb').write(response.content)
    LOGGER.info('Successfully Generated New CSR')


def import_certificate(hostname, common_name, session):
    path = os.environ['HOME']
    certificate_path = "{path}/.acme.sh/{hostname}/fullchain.cer".format(
        path=path, hostname=hostname)
    file = open(certificate_path, 'r')
    url = 'https://{hostname}/api/v3.7/services/https'.format(
        hostname=hostname)
    data = {
        'https': {
            'common_name': common_name,
            'organization': os.environ['organization'],
            'cert': '{cert}'.format(cert=file.read()),
            'key_length': 2048,
            'csr': {
                'country': os.environ['country'],
                'state': os.environ['state'],
                'locality': os.environ['locality'],
                'common_name': common_name,
                'email': os.environ['email'],
                'key_length': 2048,
                'organization': os.environ['organization'],
                'org_unit': os.environ['organization_unit']
            }
        }
    }
    file.close()

    headers = {'Authorization': 'Token {session}'.format(session=session)}
    response = acme_request.put(url, headers=headers, data=json.dumps(data))
    LOGGER.info("Lighthouse Successfully Imported the New Certificate")


def main():
    requests.packages.urllib3.disable_warnings()
    global acme_request

    region_name = os.environ['AWS_REGION']
    hostname = os.environ['SYSTEM_NAME']
    common_name = os.environ['COMMON_NAME']
    dns = os.environ['ACME_DNS']
    prefix = os.environ['PREFIX']
    validation = os.environ['VALIDATE_CERTIFICATE']

    username = acme.get_secret(
        f'{prefix}/otter/lighthouse', 'username')
    password = acme.get_secret(
        f'{prefix}/otter/lighthouse', 'password')

    acme_request = acme.Request(validation=validation)

    subject_alternative_names = acme.query_subject_alternative_names(
        hostname)

    le_client = acme.LetsEncrypt(
        hostname=hostname,
        common_name=common_name,
        subdelegate=dns,
        subject_alternative_names=subject_alternative_names,
        region=region_name)

    session = generate_api_token(hostname, username, password)
    generate_csr(hostname, common_name, session)

    path = os.environ['HOME']
    le_client.acme_production(csr=f'{path}/output.csr')


    import_certificate(hostname, common_name, session)
    time.sleep(60)

    expiration = acme.query_certificate_expiration(hostname, common_name)
    acme.update_certificate_expiration(hostname, expiration)


if __name__ == '__main__':
    main()
