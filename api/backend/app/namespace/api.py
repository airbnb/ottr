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
import dateutil
import tldextract
from datetime import datetime, timedelta

from flask import abort, request
from flask_restx import Resource

from backend.app.namespace.authorization import validate_token_header
from backend.app.shared.client import query_acme_challenge_records
from backend.app.shared.network import Device
from backend.app.shared import client
from backend.app.models import (api_namespace, authentication_parser,
                                asset_output, asset_input,
                                developer_permissions,
                                privileged_permissions,
                                admin_permissions, PUBLIC_KEY)

# HTTP Status Codes: https://docs.python.org/3/library/http.html

CONF_ROUTE_FILE = os.path.join(
    os.path.dirname(__file__), '../config/route.json')

dynamodb_client = client.DynamoDBClient(
    region_name=os.environ['AWS_DEFAULT_REGION'], table_name=os.environ['TABLE'])


def authentication_header_parser(value, secret):
    data = validate_token_header(value, secret)
    if data is None:
        abort(401)
    return data


def filter(primary_index, secondary_index):
    system_names = {d['system_name'] for d in primary_index}
    output = [x for x in secondary_index if x['system_name'] in system_names]
    return output


def query_expired_certificates(days_until_expiration):
    response = dynamodb_client.scan_table()
    data = response['Items']
    expired_certificates = list()
    days_until_expiration = int(days_until_expiration)

    for host in data:
        if host['certificate_expiration'] != 'None':

            expiration_calculation = (dateutil.parser.parse(
                host['certificate_expiration']) - timedelta(days=days_until_expiration)).isoformat()

            if datetime.utcnow().isoformat() > expiration_calculation:
                expired_certificates.append(host)

    return expired_certificates


@api_namespace.route('/v1/search', methods=['GET'])
class Search(Resource):
    @api_namespace.expect(authentication_parser)
    @api_namespace.doc('search', responses={403: 'Invalid Role'}, params={'host_platform': {'description': 'Host OS Platform', 'in': 'query', 'type': 'str', 'required': False}, 'data_center': {'description': 'Data Center', 'in': 'query', 'type': 'str', 'required': False}, 'ip_address': {'description': 'IPv4 Address: [10.0.0.1]', 'in': 'query', 'type': 'str', 'required': False}, 'system_name': {'description': 'System Name: [subdomain.example.com]', 'in': 'query', 'type': 'str', 'required': False}, 'days_until_expiration': {'description': 'Number of Days (i.e. 30) Or Less Days Until Certificate Expires', 'in': 'query', 'type': 'int', 'required': False}, 'origin': {'description': 'Source of Asset: [API]', 'in': 'query', 'type': 'str', 'required': False}}, description='Search Asset Inventory')
    @api_namespace.response(model=asset_output, code=200, description='Success', as_list=True)
    def get(self):
        args = authentication_parser.parse_args()
        role = authentication_header_parser(
            args['Authorization'], PUBLIC_KEY)

        try:
            if role in developer_permissions:
                ip_address = request.args.get('ip_address')
                system_name = request.args.get('system_name')
                data_center = request.args.get('data_center')
                host_platform = request.args.get('host_platform')
                days_until_expiration = request.args.get(
                    'days_until_expiration')
                origin = request.args.get('origin')

                conversion = {
                    'ip_address': ip_address,
                    'system_name': system_name,
                    'data_center': data_center,
                    'host_platform': host_platform,
                    'origin': origin
                }
                query = ['ip_address', 'system_name',
                         'data_center', 'host_platform', 'origin']
                unique_list_output = None

                # Scan Table for Expiration
                if days_until_expiration is not None:
                    unique_list_output = query_expired_certificates(
                        days_until_expiration)

                    # No Certificate Expiration Match
                    if len(unique_list_output) == 0:
                        return unique_list_output

                # Query Table Based on Global Secondary Indexes
                for elem in query:
                    if conversion[elem] is not None and unique_list_output is None:
                        unique_list_output = dynamodb_client.query_index(
                            '{}_index'.format(elem), elem, conversion[elem])['Items']
                    elif conversion[elem] is not None:
                        query_output = dynamodb_client.query_index(
                            '{}_index'.format(elem), elem, conversion[elem])['Items']
                        unique_list_output = filter(
                            query_output, unique_list_output)
                    else:
                        pass

                return unique_list_output
            else:
                return {'Invalid Permissions': '{} Role Invalid'.format(role)}, 500

        except Exception as error:
            api_namespace.abort(
                500, error.__doc__, statusCode='500')


@api_namespace.route('/v1/assets', methods=['POST', 'PUT'])
class Assets(Resource):
    @api_namespace.doc('create_asset', responses={403: 'Invalid Role', 500: 'Input Validation Error'}, description='Add Device to Asset Inventory')
    @api_namespace.response(model=asset_input, code=201, description='Success')
    @api_namespace.expect(asset_input, authentication_parser)
    def post(self):
        args = authentication_parser.parse_args()
        role = authentication_header_parser(
            args['Authorization'], PUBLIC_KEY)

        if role in privileged_permissions:
            json_data = request.json
            system_name = json_data.get('system_name')
            common_name = json_data.get('common_name')
            certificate_authority = json_data.get('certificate_authority')
            data_center = json_data.get('data_center')
            device_model = json_data.get('device_model')
            host_platform = json_data.get('host_platform')
            ip_address = json_data.get('ip_address')
            os_version = json_data.get('os_version')
            subject_alternative_name = json_data.get(
                'subject_alternative_name')
            if not subject_alternative_name:
                subject_alternative_name = [common_name]

            host = Device(
                ip_address=ip_address, system_name=system_name, common_name=common_name, certificate_authority=certificate_authority, host_platform=host_platform, os_version=os_version, data_center=data_center, device_model=device_model, subject_alternative_name=subject_alternative_name, origin='API')
            device = dynamodb_client.query_primary_key(
                system_name).get('Items')
            if bool(device):
                api_namespace.abort(500, status="Device Exists: {device}".format(
                    device=system_name), statusCode='500')
            else:
                dynamodb_client.create_item(host)
            return api_namespace.marshal(host, asset_input), 201
        else:
            return {'Invalid Permissions': '{} Role Invalid'.format(role)}, 500

    @api_namespace.doc('update_asset', responses={500: 'Invalid Role', 500: 'Input Validation Error'}, description='Update Device in Asset Inventory')
    @api_namespace.response(model=asset_input, code=200, description='Success')
    @api_namespace.expect(asset_input, authentication_parser)
    def put(self):
        args = authentication_parser.parse_args()
        role = authentication_header_parser(
            args['Authorization'], PUBLIC_KEY)

        if role in privileged_permissions:
            json_data = request.json
            system_name = json_data.get('system_name')
            common_name = json_data.get('common_name')
            certificate_authority = json_data.get('certificate_authority')
            data_center = json_data.get('data_center')
            device_model = json_data.get('device_model')
            host_platform = json_data.get('host_platform')
            ip_address = json_data.get('ip_address')
            os_version = json_data.get('os_version')
            subject_alternative_name = json_data.get(
                'subject_alternative_name')
            if not subject_alternative_name:
                subject_alternative_name = [common_name]

            host = Device(
                ip_address=ip_address, system_name=system_name, common_name=common_name, certificate_authority=certificate_authority, host_platform=host_platform, os_version=os_version, data_center=data_center, device_model=device_model, subject_alternative_name=subject_alternative_name, origin='API')

            device = dynamodb_client.query_primary_key(
                system_name).get('Items')
            if bool(device):
                dynamodb_client.update_item(host)
                return api_namespace.marshal(host, asset_input), 200
            else:
                api_namespace.abort(500, status="Device Does Not Exist: {device}".format(
                    device=system_name), statusCode='500')
        else:
            return {'Invalid Permissions': '{} Role Invalid'.format(role)}, 500


@api_namespace.route('/v1/assets/delete/<string:system_name>', methods=['DELETE'])
class DeleteAsset(Resource):
    @api_namespace.expect(authentication_parser)
    @api_namespace.doc('delete_asset', responses={204: 'Success', 200: 'Invalid Host', 500: 'Invalid Role'}, description='Delete Device in Asset Inventory')
    def delete(self, system_name):
        args = authentication_parser.parse_args()
        role = authentication_header_parser(
            args['Authorization'], PUBLIC_KEY)

        if role in privileged_permissions:
            device = dynamodb_client.query_primary_key(
                system_name).get('Items')
            if not bool(device):
                return {'Invalid Host': '{}'.format(system_name)}, 200

            response = dynamodb_client.delete_item(system_name)
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                return '', 204
        else:
            return {'Invalid Permissions': '{} Role Invalid'.format(role)}, 500


@api_namespace.route('/v1/certificate/rotate/<string:system_name>', methods=['POST'])
class RotateExpiredCertificate(Resource):
    @api_namespace.expect(authentication_parser)
    @api_namespace.doc('rotate_expired_certificate', responses={200: 'Invalid Host', 204: 'Success', 403: 'Invalid Role'}, description='Rotate Certificate for Device')
    def post(self, system_name):
        args = authentication_parser.parse_args()
        role = authentication_header_parser(
            args['Authorization'], PUBLIC_KEY)

        if role in privileged_permissions:
            query = dynamodb_client.query_primary_key(system_name)
            if not query['Items']:
                return {'Invalid Host': '{}'.format(system_name)}, 200
            else:
                device = query.get('Items')[0]
                # Route53 DNS Mapping
                output = tldextract.extract(system_name)
                domain = output.domain + '.' + output.suffix
                subdomain = output.subdomain
                if not query_acme_challenge_records(domain, subdomain):
                    return {'Route53 Error': 'DNS CNAME Record Not Found for {}'.format(system_name)}, 200
                client.start_execution(device)
                return '', 204
        else:
            return {'Invalid Permissions': '{} Role Invalid'.format(role)}, 403


@api_namespace.route('/v1/management/certificate-validation/unset/<string:system_name>', methods=['PATCH'])
class UnsetCertificateValidation(Resource):
    @api_namespace.expect(authentication_parser)
    @api_namespace.doc('unset_certificate_validation', responses={200: 'Success', 403: 'Invalid Role'}, description='Set Database to Allow HTTP Requests Against Target Device with Self-Signed or Invalid Certificates')
    def patch(self, system_name):
        args = authentication_parser.parse_args()
        role = authentication_header_parser(
            args['Authorization'], PUBLIC_KEY)

        if role in admin_permissions:
            query = dynamodb_client.query_primary_key(system_name)
            if not query['Items']:
                return {'Invalid Host': '{}'.format(system_name)}, 200
            else:
                response = dynamodb_client.set_certificate_validation(system_name=system_name, status='False')
                if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                    return {f'Certificate Validation Unset': f'Certificate validation disabled for the next execution on {system_name}. Please ensure this endpoint was only executed if the current certification on {system_name} is either a self-signed or an invalid certificate.'}, 200
        else:
            return {'Invalid Permissions': '{} Role Invalid'.format(role)}, 403

@api_namespace.route('/v1/management/certificate-validation/set/<string:system_name>', methods=['PATCH'])
class SetCertificateValidation(Resource):
    @api_namespace.expect(authentication_parser)
    @api_namespace.doc('set_certificate_validation', responses={200: 'Success', 403: 'Invalid Role'}, description='Set Database to Allow Certificate Verification for HTTP Requests on Target Device')
    def patch(self, system_name):
        args = authentication_parser.parse_args()
        role = authentication_header_parser(
            args['Authorization'], PUBLIC_KEY)

        if role in admin_permissions:
            query = dynamodb_client.query_primary_key(system_name)
            if not query['Items']:
                return {'Invalid Host': '{}'.format(system_name)}, 200
            else:
                response = dynamodb_client.set_certificate_validation(system_name=system_name, status='True')
                if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                    return {f'Certificate Validation Enabled': f'Certificate validation enabled on {system_name}. Please ensure {system_name} does not currently have a self-signed or invalid certificate.'}, 200
        else:
            return {'Invalid Permissions': '{} Role Invalid'.format(role)}, 403
