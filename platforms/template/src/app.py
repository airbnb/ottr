#!/usr/local/bin/python

import os
import sys
import requests

import acme

LOGGER = acme.get_logger(__name__)

# Populate Local Environmental Variables [platform/template/config/environment.sh]:
# . ./environment.sh


def main():
    requests.packages.urllib3.disable_warnings()

    region_name = os.getenv('AWS_REGION')
    hostname = os.environ['HOSTNAME']
    common_name = os.environ['COMMON_NAME']
    dns = os.environ['ACME_DNS']
    prefix = os.environ['PREFIX']
    validation = os.environ['VALIDATE_CERTIFICATE']

    # [0] Instantiate Requests Class from ottr/acme for HTTP Requests
    # Example: acme_request.get(url=url, headers=headers, query_params=query_params)
    acme_request = acme.Request(validation=validation)

    # Pull Secrets from Secrets Manager

    # [1] Update Secrets Path (Create from Terraform Module in secrets.tf)
    username = acme.get_secret(
        f'{prefix}/otter/[PATH]', 'username', region_name)
    password = acme.get_secret(
        f'{prefix}/otter/[PATH]', 'password', region_name)

    # [2] system_name Must be in Otter DynamoDB Table
    subject_alternative_names = acme.query_subject_alternative_names(
        hostname)

    # Let's Encrypt Client/Initialization
    # [3] Host Must Have DNS Mapping to Subdelegate Zone [Example: dns/platform.tf]
    le_client = acme.LetsEncrypt(
        hostname=hostname, subdelegate=dns, subject_alternative_names=subject_alternative_names,
        region=region_name)

    # [4] Generate Public/Private Key Pair and CSR

    # [5] Pull CSR to Filesystem (Container or Local)

    # [6] Sign CSR Using Let's Encrypt as Certificate Authority

    # DEBUG: _ecc Directories for Ecliptic Curve, RSA For non _ecc Suffix
    # LOGGER.info(os.listdir('/home/otter/.acme.sh/'))

    # path [string] is Path to CSR File

    # Local Development:
    le_client.acme_local(csr='PATH_TO_CSR')

    # ECS Development:
    # le_client.acme_development(csr=path)

    # ECS Production:
    # le_client.acme_production(csr=path)

    # Certificate Path Output:
    # $HOME/.acme.sh/{hostname}/fullchain.cer


    # [7] Apply Changes to Management Console (Set Wait Period for Certificate to Propagate)

    # [8] Pull Certificate and Update DynamoDB Table
    expiration = acme.query_certificate_expiration(hostname)
    acme.update_certificate_expiration(hostname, expiration)


if __name__ == '__main__':
    main()
