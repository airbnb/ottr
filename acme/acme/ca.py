"""
Copyright 2021-present Airbnb, Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
   http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import shutil
import subprocess
import requests
import sys
import socket
from typing import List

import boto3
import tldextract
import nmap

from .logger import get_logger
from .client import get_secret


LOGGER = get_logger(__name__)


class LetsEncrypt:
    def __init__(self, hostname: str, subdelegate: str, subject_alternative_names: List[str], region: str) -> None:
        self.subdelegate = subdelegate
        self.region = region
        self.hostname = self._validate_device_connection(hostname)
        self.subdomain = self._get_subdomain(hostname)
        self.subject_alternative_names = self._validate_subdelegate_zone(
            subject_alternative_names)

    def _get_subdomain(self, hostname: str) -> str:
        return tldextract.extract(
            self.hostname).subdomain

    def _query_acme_challenge_records(self, hostname: str, hosted_zone_id: str) -> bool:
        client = boto3.client('route53')
        paginator = client.get_paginator(
            'list_resource_record_sets')
        try:
            for page in paginator.paginate(HostedZoneId=hosted_zone_id):
                for record in page["ResourceRecordSets"]:
                    if (f'_acme-challenge.{hostname}') in record['Name']:
                        return True
            return False
        except Exception:
            raise KeyError('HOSTED_ZONE_ID Invalid')

    def _validate_device_connection(self, hostname: str, timeout=5):
        try:
            # Validate Device is Up
            scanner = nmap.PortScanner()
            ip_address = socket.gethostbyname(hostname)
            scanner.scan(ip_address, '1', '-v')
            self._register_lets_encrypt_account()
            return hostname
        except requests.ConnectionError:
            raise Exception(
                "Failed Connection to Host: {}".format(hostname))

    def _validate_subdelegate_zone(self, subject_alternative_names: List[str]) -> None:
        client = boto3.client('route53')
        for hostname in subject_alternative_names:
            # TODO: Update Other Function to Use registered_domain
            subdomain = tldextract.extract(hostname).registered_domain
            hosted_zone_id = client.list_hosted_zones_by_name(
                DNSName=f'{subdomain}.',
                MaxItems='1'
            )['HostedZones'][0]['Id'].split('/')[-1]
            if not self._query_acme_challenge_records(hostname, hosted_zone_id):
                LOGGER.warning('Invalid Challenge Alias: {hostname}'.format(
                    hostname=hostname))
                raise SystemExit(f'HOSTED_ZONE_ID Invalid for {hostname}')

    def _register_lets_encrypt_account(self) -> None:
        prefix = os.environ['PREFIX']
        home = os.environ['HOME']
        try:
            source_dir = "acme-v02.api.letsencrypt.org"
            acme_account = f"{home}/.acme.sh/ca/{source_dir}"
            if not os.path.exists(acme_account):
                os.makedirs(acme_account)

            account_json = get_secret(
                f'{prefix}/otter/account.json', element=None, region=self.region)
            with open('account.json', 'w') as outfile:
                outfile.write(account_json)
            account_key = get_secret(
                f'{prefix}/otter/account.key', region=self.region)
            with open('account.key', 'w') as outfile:
                outfile.write(account_key)

            ca_conf = get_secret(f'{prefix}/otter/ca.conf', region=self.region)
            with open('ca.conf', 'w') as outfile:
                outfile.write(ca_conf)

            shutil.move("account.json",
                        "{acme_account}/account.json".format(acme_account=acme_account))
            shutil.move("account.key",
                        "{acme_account}/account.key".format(acme_account=acme_account))
            shutil.move(
                "ca.conf", "{acme_account}/ca.conf".format(acme_account=acme_account))
        except Exception:
            message = 'ACME Account Binding Error.'
            LOGGER.error(message)
            sys.exit(1)

    def acme_development(self, csr: str) -> None:  # pragma: no cover
        subprocess.call(
            '{directory}/acme.sh/acme.sh --upgrade -b dev'.format(directory=os.getenv('HOME')), shell=True)
        subprocess.call('{directory}/acme.sh/acme.sh --set-default-ca --test --signcsr --csr {csr} --dns dns_aws --challenge-alias {domain_validation} --preferred-chain "Fake LE Root X2" --force'.format(
            directory=os.getenv('HOME'), csr=f'{csr}', domain_validation=f'{self.subdomain}.{self.subdelegate}'), shell=True)

    def acme_production(self, csr: str) -> None:  # pragma: no cover
        subprocess.call(
            '{directory}/acme.sh/acme.sh --upgrade'.format(directory=os.getenv('HOME')), shell=True)
        subprocess.call('{directory}/acme.sh/acme.sh --set-default-ca --server letsencrypt --preferred-chain "ISRG" --signcsr --csr {csr} --dns dns_aws --challenge-alias {domain_validation} --force'.format(
            directory=os.getenv('HOME'), csr=f'{csr}', domain_validation=f'{self.subdomain}.{self.subdelegate}'), shell=True)

    def acme_local(self, csr: str) -> None:  # pragma: no cover
        subprocess.call(
            '{directory}/.acme.sh/acme.sh --upgrade -b dev'.format(directory=os.getenv('HOME')), shell=True)
        subprocess.call('{directory}/.acme.sh/acme.sh --set-default-ca --test --signcsr --csr {csr} --dns dns_aws --challenge-alias {domain_validation} --preferred-chain "Fake LE Root X2" --force'.format(
            directory=os.getenv('HOME'), csr=f'{csr}', domain_validation=f'{self.subdomain}.{self.subdelegate}'), shell=True)
