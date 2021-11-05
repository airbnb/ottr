#!/usr/local/bin/python

import os
import sys
import boto3
import time
import acme

from botocore.exceptions import ClientError, WaiterError

LOGGER = acme.get_logger(__name__)

# AWS SSM Client
SSM_CLIENT = boto3.client('ssm')

def generate_csr(hostname, common_name, metadata, subject_alternative_names, path):
    """
    Use AWS SSM Run Commands to generate a private key and CSR
    on the system and output the CSR value to generate a new
    certificate.

    """
    cert_root_path = path
    cert_parent_dir = "certs"

    commandList = []

    # Check if sans are provided
    if len(subject_alternative_names) > 0:
        # If sans are provided, iterate through them
        # and create a formatted string for use with
        # the openssl command
        sans = []
        for san in subject_alternative_names:
            entry = "DNS:{san}".format(san=san)
            sans.append(entry)
        sans_string = ",".join(sans)

        if metadata['PlatformName'] == "Ubuntu":
            commandList.append('mkdir -p {path}'.format(path=os.path.join(cert_root_path, cert_parent_dir)))
            commandList.append('( cat /etc/ssl/openssl.cnf ; echo \"\\n[SAN]\\nsubjectAltName={sans}\"; ) > {path}'.format(sans=sans_string, path=os.path.join(cert_root_path, cert_parent_dir, "config")))
        elif metadata['PlatformName'] == "CentOS Linux":
            commandList.append('mkdir -p {path}'.format(path=os.path.join(cert_root_path, cert_parent_dir)))
            commandList.append('( cat /etc/pki/tls/openssl.cnf ; echo -e \"\\n[SAN]\\nsubjectAltName={sans}\"; ) > {path}'.format(sans=sans_string, path=os.path.join(cert_root_path, cert_parent_dir, "config")))
        else:
            LOGGER.error('Platform {platform} is not supported.'.format(metadata['PlatformName']))
            sys.exit(1)

        commandList.append('openssl req -nodes -newkey rsa:2048 -keyout {private_key_path} -subj "/C={country}/ST={state}/L={locality}/O={organization}/OU={org_unit}/CN={common_name}/emailAddress={email}" -reqexts SAN -config config'.format(private_key_path=os.path.join(cert_root_path, cert_parent_dir, "{}.key".format(hostname)), country=os.environ['country'], state=os.environ['state'], locality=os.environ['locality'], organization=os.environ['organization'], org_unit=os.environ['organization_unit'], common_name=common_name, email=os.environ['email']))
        commandList.append('rm -rf config')
    else:
        # Omit sans portion of openssl command
        commandList.append('openssl req -nodes -newkey rsa:2048 -keyout {private_key_path} -subj "/C={country}/ST={state}/L={locality}/O={organization}/OU={org_unit}/CN={common_name}/emailAddress={email}"'.format(private_key_path=os.path.join(cert_root_path, cert_parent_dir, "{}.key".format(hostname)), country=os.environ['country'], state=os.environ['state'], locality=os.environ['locality'], organization=os.environ['organization'], org_unit=os.environ['organization_unit'], common_name=common_name, email=os.environ['email']))

    # Generate SSM run command parameters
    parameters = {}
    parameters["commands"] = commandList

    # Send the run command to the target system and
    # grab the CSR from the output
    invocation = _send_run_command(metadata['InstanceId'], parameters)
    local_path = os.environ['HOME']
    csr_path = "{path}/csr".format(path=local_path)

    # Write the CSR to a file
    open(csr_path, 'wb').write(invocation['StandardOutputContent'].encode())

    LOGGER.info('Successfully generated new CSR')

def import_certificate(hostname, metadata, path):
    """
    Use AWS SSM Run Commands to import the certificates
    to the system.

    """
    local_path = os.environ['HOME']

    cert_root_path = path
    cert_parent_dir = "certs"

    # Generate SSM run command parameters
    commandList = []
    parameters = {}

    # Read the certificate contents from the path
    certificate_paths = [
        "{path}/.acme.sh/{hostname}/fullchain.cer".format(
        path=local_path, hostname=hostname),
        "{path}/.acme.sh/{hostname}/ca.cer".format(
        path=local_path, hostname=hostname),
        "{path}/.acme.sh/{hostname}/{hostname}.cer".format(
        path=local_path, hostname=hostname),
    ]

    # Iterate through paths to generate command list parameter
    for path in certificate_paths:
        cert = open(path, 'r')
        cert_contents = cert.read()
        cert.close()
        commandList.append('echo \"{cert}\" > {cert_path}'.format(cert=cert_contents, cert_path=os.path.join(cert_root_path, cert_parent_dir, os.path.basename(path))))

    # Add command list to commands parameter
    parameters["commands"] = commandList

    # Send the run command to the target system to
    # copy the cert contents to a file
    _send_run_command(metadata['InstanceId'], parameters)

    LOGGER.info("Successfully imported the new certificates")

def get_system_metadata(hostnames):
    """
    Get system metadata from AWS SSM managed system inventory

    """
    for hostname in hostnames:
        system_name = hostname.split(".")[0]
        try:
            response = SSM_CLIENT.describe_instance_information(
                Filters=[
                    {
                        'Key': 'tag:Name',
                        'Values': [
                            system_name,
                        ]
                    },
                ]
            )

            # Check to see if multiple systems match the given filter
            # criteria and return an error if so
            if len(response['InstanceInformationList']) == 1:
                message = 'System found with a matching name of: `{system_name}`'.format(
                system_name=hostname)
                LOGGER.info(message)

                if response['InstanceInformationList'][0]['PingStatus'] != "Online":
                    message = 'The system is not online or the AWS SSM Agent is not functioning properly.'
                    LOGGER.error(message)
                    sys.exit(1)
            elif len(response['InstanceInformationList']) > 1:
                message = 'There are multiple systems with a matching name of: `{system_name}`'.format(
                system_name=hostname)
                LOGGER.error(message)
                sys.exit(1)

            return response['InstanceInformationList'][0]
        except IndexError as error:
            message = 'There are no systems with a matching name of: `{system_name}`'.format(
            system_name=hostname)
            LOGGER.info(message)
            continue

    message = 'There are no systems matching any of the provided hostnames: {hostnames}'.format(
    hostnames=hostname)
    LOGGER.error(message)
    sys.exit(1)


def run_hooks(instance_id, path):
    """
    Run all scripts in path in alphabetical order

    """
    LOGGER.info("Running scripts in {}...".format(path))

    # Generate SSM run command parameters
    commandList = []
    commandList.append('mkdir -p {path}'.format(path=path))
    commandList.append('touch {path}/template.sh'.format(path=path))
    commandList.append('for each in {path}/*.sh ; do bash $each || exit ; done'.format(path=path))

    parameters = {}
    parameters["commands"] = commandList

    # Send the run command to the target system to
    # run all scripts in alphabetical order in the provided
    # path
    _send_run_command(instance_id, parameters)

    LOGGER.info("Successfully ran all scripts in {}".format(path))


def _get_cert_root_path(metadata):
    """
    Wait for AWS SSM Run Command to be executed on system

    """
    if metadata['PlatformName'] == "Ubuntu":
        cert_root_path = "/etc/ssl"
    elif metadata['PlatformName'] == "CentOS Linux":
        cert_root_path = "/etc/pki/tls"
    else:
        LOGGER.error('Platform {platform} is not supported.'.format(metadata['PlatformName']))
        sys.exit(1)

    return cert_root_path

def _wait_for_success(command_id, instance_id):
    """
    Wait for AWS SSM Run Command to be executed on system

    """
    LOGGER.debug('Waiting for run command {} to complete...'.format(command_id))
    try:
        waiter = SSM_CLIENT.get_waiter('command_executed')

        waiter.wait(
            CommandId=command_id,
            InstanceId=instance_id
        )

        return _get_command_status(command_id, instance_id)
    except WaiterError as error:
        invocation = _get_command_status(command_id, instance_id)
        message = 'Run Command {command_id} failed with error: {error}'.format(
            command_id=command_id, error=invocation['StandardErrorContent'])
        LOGGER.error(message)
        sys.exit(1)
    except Exception as error:
        message = 'Run Command {command_id} failed'.format(
            command_id=command_id)
        LOGGER.error(message, error)
        sys.exit(1)

def _send_run_command(instance_id, parameters):
    """
    Send run command to target systems

    """
    LOGGER.debug('Sending run command to {} system...'.format(instance_id))
    try:
        response = SSM_CLIENT.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            DocumentVersion='$DEFAULT',
            TimeoutSeconds=240,
            Parameters=parameters,
            CloudWatchOutputConfig={
                'CloudWatchLogGroupName': "/aws/ssm/AWS-RunShellScript",
                'CloudWatchOutputEnabled': True
            }
        )
        LOGGER.debug('Send Command Response: {}'.format(response))

    except ClientError as err:
        if 'ThrottlingException' in str(err):
            LOGGER.warning('RunCommand throttled, automatically retrying...')
            return _send_run_command(instance_id, parameters)
        else:
            LOGGER.error('Send Run Command function failed!\n{}'.format(str(err)))
            sys.exit(1)

    return _wait_for_success(response['Command']['CommandId'], instance_id)

def _get_command_status(command_id, instance_id):
    """
    Get SSM run command status

    """
    LOGGER.debug('Checking SSM Run Command {0} status for {1}'.format(command_id, instance_id))

    try:
        time.sleep(5)

        invocation = SSM_CLIENT.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )

        return invocation
    except ClientError as err:
        if 'ThrottlingException' in str(err):
            LOGGER.warning('RunCommand throttled, automatically retrying...')
            return _get_command_status(command_id, instance_id)
        else:
            LOGGER.error('Get SSM Command Status function failed!\n{}'.format(str(err)))
            sys.exit(1)

def main():
    region_name = os.environ['AWS_REGION']
    hostname = os.environ['SYSTEM_NAME']
    common_name = os.environ['COMMON_NAME']
    dns = os.environ['ACME_DNS']
    local_path = os.environ['HOME']
    remote_path = "/opt/otter"
    hooks_path = os.path.join(remote_path, "hooks")

    subject_alternative_names = acme.query_subject_alternative_names(
        hostname)

    le_client = acme.LetsEncrypt(
        hostname=hostname, subdelegate=dns, subject_alternative_names=subject_alternative_names,
        region=region_name)

    hostnames = subject_alternative_names
    hostnames.insert(0, hostname)

    system_metadata = get_system_metadata(hostnames)

    # Run scripts before new certificates are created
    run_hooks(system_metadata['InstanceId'], os.path.join(hooks_path, "pre"))

    generate_csr(hostname, common_name, system_metadata, subject_alternative_names, remote_path)

    le_client.acme_production(csr=f'{local_path}/csr')

    import_certificate(hostname, system_metadata, remote_path)

    expiration = acme.query_certificate_expiration(hostname)
    acme.update_certificate_expiration(hostname, expiration)

    # Run scripts after new certificate is created and uploaded
    # to the system
    run_hooks(system_metadata['InstanceId'], os.path.join(hooks_path, "post"))

if __name__ == '__main__':
    main()
