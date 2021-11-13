#!/usr/local/bin/python

import sys
import os
from datetime import datetime
from time import sleep

import requests
import defusedxml.ElementTree as etree
import acme

LOGGER = acme.get_logger(__name__)


def paloalto_keygen(hostname, username, password):
    cmd = "/api/?type=keygen&"
    url = "https://{host}{command}user={username}&password={password}".format(
        host=hostname, command=cmd, username=username, password=password)
    response = acme_request.get(url=url)
    LOGGER.info('Palo Alto Keygen HTTP Response %s', response.status_code)
    content = (response.content).decode('utf-8')
    output = etree.fromstring(content)
    api_key = output[0][0].text
    return api_key


def generate_certificate_signing_request(hostname, common_name, api_token, certificate_name, subject_alternative_names):
    pan_subject_alternative_names = ''
    for hostname in subject_alternative_names:
        pan_subject_alternative_names = pan_subject_alternative_names + \
            '<member>{hostname}</member>'.format(hostname=hostname)
    country = os.environ['country']
    state = os.environ['state']
    locality = os.environ['locality']
    organization = os.environ['organization']
    organization_unit = os.environ['organization_unit']
    cmd = f"<request><certificate><generate><certificate-name>{certificate_name}</certificate-name><name>{common_name}</name><algorithm><RSA><rsa-nbits>2048</rsa-nbits></RSA></algorithm><digest>sha256</digest><country-code>{country}</country-code><state>{state}</state><locality>{locality}</locality><organization>{organization}</organization><organization-unit><member>{organization_unit}</member></organization-unit><ca>no</ca><hostname>{pan_subject_alternative_names}</hostname><signed-by>external</signed-by></generate></certificate></request>"
    url = "https://{host}/api/?type=op&cmd={cmd}".format(
        host=hostname, cmd=cmd)
    headers = {'X-PAN-KEY': api_token}
    response = acme_request.get(url=url, headers=headers)
    output = (response.content).decode("utf-8")
    LOGGER.info('Generate CSR Response: %s', output)
    return response


def get_certificate_signing_request_data(hostname, api_token, certificate_name):
    cmd = "type=export&category=certificate&certificate-name={certificate_name}&format={format}&include-key=no".format(
        certificate_name=certificate_name, format='pkcs10')
    url = "https://{host}/api/?{cmd}".format(host=hostname, cmd=cmd)
    headers = {'X-PAN-KEY': api_token}
    response = acme_request.get(url=url, headers=headers)
    LOGGER.info('Get CSR Data HTTP Response %s', response.status_code)

    # CSR Validation
    output = (response.content).decode("utf-8")
    LOGGER.info('CSR Output:\n%s', output)

    csr_output = open(f"{certificate_name}.csr", "wt")
    csr_output.write(output)
    csr_output.close()


def import_certificate(hostname, api_token, certificate_name):
    path = os.environ['HOME']
    certificate_path = "{path}/.acme.sh/{hostname}/fullchain.cer".format(
        path=path, hostname=hostname)
    files = {'file': open(certificate_path, 'rb')}
    cmd = 'import&category=certificate&certificate-name={0}&format=pem'.format(
        certificate_name)
    url = 'https://{hostname}/api/?type={cmd}'.format(
        hostname=hostname, cmd=cmd)
    headers = {'X-PAN-KEY': api_token}
    response = acme_request.post(url=url, headers=headers,
                             files=files)
    output = (response.content).decode("utf-8")
    LOGGER.info(output)
    return response


def set_tls_service_profile(hostname, api_token, certificate_name):
    cmd = "type=config&action=set&xpath=/config/shared/ssl-tls-service-profile/entry[@name='otter']&element=<protocol-settings><min-version>tls1-2</min-version><max-version>max</max-version></protocol-settings><certificate>{certificate_name}</certificate>".format(
        certificate_name=certificate_name)
    url = "https://{host}/api/?{cmd}".format(host=hostname, cmd=cmd)
    headers = {'X-PAN-KEY': api_token}
    response = acme_request.get(url=url, headers=headers)
    LOGGER.info('Set TLS Service Profile HTTP Response %s',
                response.status_code)
    return response


def set_management_plane(hostname, api_token):
    cmd = "type=config&action=set&xpath=/config/devices/entry[@name='localhost.localdomain']/deviceconfig/system&element=<ssl-tls-service-profile>otter</ssl-tls-service-profile>"
    url = "https://{host}/api/?{cmd}".format(host=hostname, cmd=cmd)
    headers = {'X-PAN-KEY': api_token}
    response = acme_request.get(url=url, headers=headers)
    LOGGER.info('Set Management Plane HTTP Response %s', response.status_code)
    return response


def commit_changes(username, hostname, api_token):
    cmd = "type=commit&action=partial&cmd=<commit><partial><admin><member>{username}</member></admin></partial></commit>".format(
        username=username)
    url = "https://{host}/api/?{cmd}".format(host=hostname, cmd=cmd)
    headers = {'X-PAN-KEY': api_token}
    response = acme_request.get(url=url, headers=headers)
    LOGGER.info('Commit Changes HTTP Response %s', response.status_code)

    output = (response.content).decode("utf-8")
    job_id = xml_parser(output, '<job>', '</job>')

    # Queue PAN Commit Status
    pending = True
    count = 0
    while pending is True:
        if count >= 600:
            LOGGER.error('PanOS Commit Exceeded Bound Time')
            sys.exit(1)
        cmd = "type=op&cmd=<show><jobs><id>{job_id}</id></jobs></show>".format(
            job_id=job_id)
        url = "https://{host}/api/?{cmd}".format(
            api_key=api_token, host=hostname, cmd=cmd)
        headers = {'X-PAN-KEY': api_token}
        response = acme_request.get(url=url, headers=headers)
        output = (response.content).decode("utf-8")
        status = xml_parser(output, '<status>', '</status>')
        if status == 'FIN':
            pending = False
        count += 1
        sleep(60)
        LOGGER.info(status)


def xml_parser(output, begin, end):
    start = output.index(begin) + len(begin)
    end = output.index(end, start)
    job_id = (output[start:end])
    return job_id


def save_running_config(hostname, api_token):
    cmd = "type=export&category=configuration"
    url = "https://{host}/api/?{cmd}".format(host=hostname, cmd=cmd)
    headers = {'X-PAN-KEY': api_token}
    response = acme_request.get(url=url, headers=headers)
    LOGGER.info('Export Running Config HTTP Response %s', response.status_code)

    with open('/tmp/config.xml', 'wb') as handle:
        for block in response.iter_content(1024):
            handle.write(block)


def get_palo_alto_certificates(hostname, api_token):
    cmd = 'type=config&action=get&xpath=/config/shared/certificate'
    url = "https://{host}/api/?{cmd}".format(host=hostname, cmd=cmd)
    headers = {'X-PAN-KEY': api_token}
    response = acme_request.get(url=url, headers=headers)
    content = (response.content).decode('utf-8')
    LOGGER.info('Get Palo Alto Certificates HTTP Response %s',
                response.status_code)
    root = etree.fromstring(content)
    certificates = []
    if root.find('.//certificate') is None:
        pass
    else:
        for node in root.find('.//certificate'):
            if 'otter' in node.attrib['name']:
                certificates.append(node.attrib['name'])
    return certificates


def delete_certificates(hostname, api_token, certificates):
    if not certificates:
        return
    for certificate in certificates:
        cmd = 'type=config&action=delete&xpath=/config/shared/certificate/entry[@name=\'{certificate}\']'.format(
            certificate=certificate)
        url = "https://{host}/api/?{cmd}".format(host=hostname, cmd=cmd)
        headers = {'X-PAN-KEY': api_token}
        response = acme_request.get(url, headers=headers)
        content = (response.content).decode('utf-8')
        LOGGER.info('Certificate: %s %s', certificate, content)


def main():
    requests.packages.urllib3.disable_warnings()
    global acme_request

    hostname = os.environ['SYSTEM_NAME']
    common_name = os.environ['COMMON_NAME']
    region_name = os.environ['AWS_REGION']
    dns = os.environ['ACME_DNS']
    prefix = os.environ['PREFIX']
    validation = os.environ['VALIDATE_CERTIFICATE']

    username = acme.get_secret(
        f'{prefix}/otter/panos', 'username', region_name)
    password = acme.get_secret(
        f'{prefix}/otter/panos', 'password', region_name)

    header = 'Host: [{}]'.format(hostname)
    LOGGER.info(header)

    acme_request = acme.Request(validation=validation)

    subject_alternative_names = acme.query_subject_alternative_names(
        hostname)

    le_client = acme.LetsEncrypt(
        hostname=hostname,
        common_name=common_name,
        subdelegate=dns,
        subject_alternative_names=subject_alternative_names,
        region=region_name)

    api_token = paloalto_keygen(hostname, username, password)

    date_time = "{:%Y_%m_%d}".format(datetime.now())
    certificate_name = 'otter_panos_{}'.format(date_time)

    save_running_config(hostname, api_token)
    certificates = get_palo_alto_certificates(hostname, api_token)
    generate_certificate_signing_request(
        hostname, common_name, api_token, certificate_name, subject_alternative_names)
    get_certificate_signing_request_data(
        hostname, api_token, certificate_name)

    le_client.acme_production(csr=f'{certificate_name}.csr')

    import_certificate(hostname, api_token, certificate_name)
    set_tls_service_profile(hostname, api_token, certificate_name)
    set_management_plane(hostname, api_token)
    delete_certificates(hostname, api_token, certificates)
    commit_changes(username, hostname, api_token)

    expiration = acme.query_certificate_expiration(hostname, common_name)
    LOGGER.info('Certificate expires on %s', expiration)
    acme.update_certificate_expiration(hostname, expiration)


if __name__ == '__main__':
    main()
