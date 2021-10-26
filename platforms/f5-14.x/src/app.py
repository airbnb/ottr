#!/usr/local/bin/python

import os
from re import sub
import sys
import requests
import json
import time
import subprocess
import sys

import acme

LOGGER = acme.get_logger(__name__)


def restart_httpd(username, password, hostname):
    commands = ['restart /sys service httpd',
                'tmsh restart /sys service httpd']
    for command in commands:
        output = subprocess.Popen(f"sshpass -p {password} \
                                ssh {username}@{hostname} {command}",
                                  shell=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE).communicate()
        if output[0]:
            return output
    sys.exit(1)


def upload_certificate_sshpass(username, hostname, password, local_file, remote_file):
    p = subprocess.Popen([
        "sshpass",
        "-p",
        f"{password}",
        "scp",
        "-oStrictHostKeyChecking=no",
        local_file,
        f"{username}@{hostname}:{remote_file}"
    ])

    # Wait for Each Process to Finish
    while p.poll() == None:
        time.sleep(1)
        p.poll()
    (results, errors) = p.communicate()
    if errors == "" or errors == None:
        return results
    else:
        sys.exit(1)


def get_token(url, username, password):
    payload = {}
    payload.setdefault('username', username)
    payload.setdefault('password', password)
    payload.setdefault('loginProviderName', 'tmos')
    return acme_request.post(url, data=json.dumps(payload)).json()['token']['token']


def _execute_bash(command, headers, hostname):
    url = f'https://{hostname}/mgmt/tm/util/bash'
    payload = {
        "command": "run",
        "utilCmdArgs": f"-c '{command}'"
    }
    response = acme_request.post(url, headers=headers, data=json.dumps(payload)).text
    LOGGER.info(response)


def main():
    # Disable Warnings Requests Package
    requests.packages.urllib3.disable_warnings()
    global acme_request

    region_name = os.environ['AWS_REGION']
    hostname = os.environ['HOSTNAME']
    common_name = os.environ['COMMON_NAME']
    dns = os.environ['ACME_DNS']
    prefix = os.environ['PREFIX']
    validation = os.environ['VALIDATE_CERTIFICATE']

    username = acme.get_secret(
        f'{prefix}/otter/f5', 'username', region_name)
    password = acme.get_secret(
        f'{prefix}/otter/f5', 'password', region_name)

    acme_request = acme.Request(validation=validation)

    subject_alternative_names = acme.query_subject_alternative_names(
        hostname)

    le_client = acme.LetsEncrypt(
        hostname=hostname, subdelegate=dns, subject_alternative_names=subject_alternative_names,
        region=region_name)

    # Authenticate
    url_base = f'https://{hostname}/mgmt'
    url_auth = f'{url_base}/shared/authn/login'

    token = get_token(url_auth, username, password)
    headers = {
        'Content-Type': 'application/json',
        'X-F5-Auth-Token': token
    }

    certificate_name = 'otter'

    # Remove Previous Configuration
    removals = [
        f"tmsh delete sys crypto csr {certificate_name}.csr",
        f"tmsh delete sys crypto key {certificate_name}.key"
    ]
    for command in removals:
        _execute_bash(command, headers, hostname)

    # Generate Public/Private Key Pair and CSR
    url = f"https://{hostname}/mgmt/tm/sys/crypto/key"
    payload = {
        "name": f"{certificate_name}.key"
    }
    response = acme_request.post(url, headers=headers, data=json.dumps(payload))
    LOGGER.info(response.text)

    url = f"https://{hostname}/mgmt/tm/sys/crypto/csr"
    payload = {
        "name": f"{certificate_name}.csr",
        "key": f"{certificate_name}.key",
        "common-name": f"{common_name}",
        "organization": os.environ['organization'],
        "ou": os.environ['organization_unit'],
        "state": os.environ['state'],
        "city": os.environ['locality'],
        # "subject-alternative-name": "",
    }
    response = acme_request.post(url, headers=headers, data=json.dumps(payload))
    LOGGER.info(response.text)

    # Pull CSR to Filesystem (Container or Local)
    url = f'https://{hostname}/mgmt/tm/util/bash'
    payload = {
        "command": "run",
        "utilCmdArgs": f"-c 'tmsh list sys crypto csr {certificate_name}.csr'"
    }
    response = acme_request.post(url, headers=headers, data=json.dumps(payload))
    csr_output = json.loads(
        response.text).get('commandResult')
    begin_request = '-----BEGIN CERTIFICATE REQUEST-----'
    end_request = '-----END CERTIFICATE REQUEST-----'
    begin = csr_output.rindex(begin_request) + len(begin_request)
    end = csr_output.rindex(end_request, begin)
    certificate_signing_request = begin_request + \
        csr_output[begin:end] + end_request

    with open(f"{certificate_name}.csr", "wt") as file:
        file.write(certificate_signing_request)

    # Sign CSR Using Let's Encrypt as Certificate Authority
    le_client.acme_production(csr=f'{certificate_name}.csr')

    # Private Key Location
    url = f'https://{hostname}/mgmt/tm/adc/fileobject/ssl-key'
    response = json.loads(acme_request.get(url, headers=headers).text)

    for item in response['items']:
        name = item.get('name')
        if name == f'{certificate_name}.key':
            private_key_path = item.get('cachePath')
            break

    home = os.environ['HOME']
    os.system(
        f'openssl x509 -inform PEM -in {home}/.acme.sh/{hostname}/fullchain.cer -out ./{certificate_name}.crt')

    upload_certificate_sshpass(username, hostname, password,
                               f'{certificate_name}.crt', f'/var/tmp/{certificate_name}.crt')
    LOGGER.info("Certificate Pushed")

    try:
        steps = [
            'cp /config/httpd/conf/ssl.crt/server.crt /config/httpd/conf/ssl.crt/server.crt.backup',
            'cp /config/httpd/conf/ssl.key/server.key /config/httpd/conf/ssl.key/server.key.backup',
            f'cp {private_key_path} /config/httpd/conf/ssl.key/server.key',
            f'cp /var/tmp/{certificate_name}.crt /config/httpd/conf/ssl.crt/server.crt',
        ]
        for command in steps:
            _execute_bash(command, headers, hostname)

        output = restart_httpd(username, password, hostname)
        LOGGER.info(output)

        # Update DynamoDB Table
        expiration = acme.query_certificate_expiration(hostname)
        acme.update_certificate_expiration(hostname, expiration)
    # Revert Logic
    except Exception as error:
        steps = [
            'cp /config/httpd/conf/ssl.crt/server.crt.backup /config/httpd/conf/ssl.crt/server.crt',
            'cp /config/httpd/conf/ssl.key/server.key.backup /config/httpd/conf/ssl.key/server.key',
        ]
        for command in steps:
            _execute_bash(command, headers, hostname)

        output = restart_httpd(username, password, hostname)
        LOGGER.info(output)

        message = 'Error Restarting httpd on `{hostname}`. Reverted Previous State.'.format(
            hostname=hostname)
        LOGGER.error(message, error)
        sys.exit(1)

    # F5 Device Certificate Locations
    # /config/ssl/ssl.key/server.key
    # /config/ssl/ssl.crt/server.crt

    # Revert: https://support.f5.com/csp/article/K12522815#view
    # openssl req -x509 -nodes -newkey rsa:2048 -keyout /config/httpd/conf/ssl.key/server.key -out /config/httpd/conf/ssl.crt/server.crt -days 365
    # tmsh restart /sys service httpd

    # Force Reset
    # killall -9 httpd
    # tmsh start sys service httpd


if __name__ == '__main__':
    main()
