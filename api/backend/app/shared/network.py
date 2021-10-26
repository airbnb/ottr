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

import json
import os
import logging

import tldextract
import boto3

from backend import app


logger = logging.getLogger(__name__)
CONF_ROUTE_FILE = os.path.join(
    os.path.dirname(__file__), '../config/route.json')


region = os.environ['AWS_DEFAULT_REGION']
table_name = os.environ['TABLE']
dynamodb = boto3.resource(
    'dynamodb', region_name=region)
table = dynamodb.Table(table_name)


class Device:
    def __init__(self, ip_address='None', system_name='None', host_platform='None', os_version='None', device_model='None', certificate_authority='None', data_center='None', subject_alternative_name=[], origin='None', common_name='None', validate_certificate='True') -> None:
        self._metadata()
        self.ip_address = ip_address
        self.certificate_authority = certificate_authority
        self.data_center = data_center
        self.host_platform = host_platform
        self.os_version = os_version
        self.system_name = system_name
        self.device_model = device_model
        self.subject_alternative_name = subject_alternative_name
        self.origin = origin
        self.common_name = common_name
        self.validate_certificate = validate_certificate

    def __str__(self):
        structure = f"{{ip_address: {self.ip_address}, system_name: {self.system_name}, common_name: {self.common_name}, host_platform: {self.host_platform}, os_version: {self.os_version}, device_model: {self.device_model}, certificate_authority: {self.certificate_authority}, data_center: {self.data_center}, subject_alternative_name: {self.subject_alternative_name}, validate_certificate: {self.validate_certificate}}}"
        return structure

    def _metadata(self) -> None:
        with open(CONF_ROUTE_FILE) as file:
            output = json.load(file)
            self.supported_certificate_authority = output['certificate_authorities']
            self.valid_domains = list(output['hosted_zones'])

            platforms = []
            for platform in output['platform']:
                platforms.append(platform)

            self.supported_host_platforms = platforms

    def _toJSON(self) -> dict:
        return json.dumps(self, default=lambda elem: elem.__dict__,
                          sort_keys=True, indent=4)

    @property
    def host_platform(self):
        """ host_platform.setter validates that your OS Platform (i.e. panos,
            f5, etc.) is included within the config file config/route.json. If
            an object with an invalid OS is added an exception will be thrown.

        Returns:
            Validates OS, exception will be thrown with an invalid input
            that is not within config/route.json.
        """
        return self._host_platform

    @host_platform.setter
    def host_platform(self, value):
        self._host_platform = value
        if not isinstance(value, str):
            app.api_namespace.abort(
                500, status=f"host_platform {self._host_platform} required to be a string (str)", statusCode='500')
        if self._host_platform not in self.supported_host_platforms:
            app.api_namespace.abort(
                500, status=f"host_platform {self._host_platform} not supported, valid parameters include: {self.supported_host_platforms}", statusCode='500')

    @property
    def certificate_authority(self):
        """certificate_authority.setter validates that your Certificate
            Authority (i.e. lets_encrypt) is included within the config file
            config/route.json. If an object with an invalid CA is added an
            exception will be thrown.

        Returns:
            Validates CA, exception will be thrown with an invalid input that
            is not within config/route.json.
        """
        return self._certificate_authority

    @certificate_authority.setter
    def certificate_authority(self, value):
        self._certificate_authority = value

        if not isinstance(value, str):
            app.api_namespace.abort(
                500, status=f"certificate_authority {self._certificate_authority} required to be a string (str)", statusCode='500')
        if self._certificate_authority not in self.supported_certificate_authority:
            app.api_namespace.abort(
                500, status="certificate_authority {var} not supported, valid parameters include: {certificate_authority}".format(
                    var=self._certificate_authority, certificate_authority=self.supported_certificate_authority), statusCode='500')

    @property
    def system_name(self):
        """system_name.setter validates that your Fully Qualified Domain
            Name (FQDN) (i.e. test.example.com) is in a valid format. If an
            object with an invalid FQDN is added an exception will be thrown.

        Returns:
            Validates FQDN, exception will be thrown if format is incorrect.
        """
        return self._system_name

    @system_name.setter
    def system_name(self, value):
        self._system_name = value
        if not isinstance(value, str):
            app.api_namespace.abort(
                500, status=f"system_name {self._system_name} required to be a string (str)", statusCode='500')
        if self._system_name != 'None':
            if not bool(tldextract.extract(self._system_name).suffix):
                app.api_namespace.abort(500, status="system_name Does Not Contain a FQDN: {}".format(
                    self._system_name), statusCode='500')
            domain = '{domain}.{suffix}'.format(domain=tldextract.extract(
                self._system_name).domain, suffix=tldextract.extract(self._system_name).suffix)
            if domain not in self.valid_domains:
                app.api_namespace.abort(500, status="system_name {} Not a Valid Domain: {}".format(
                    self._system_name, self.valid_domains), statusCode='500')
        else:
            app.api_namespace.abort(
                500, status="system_name Empty, Please Provide a FQDN.", statusCode='500')

    @property
    def common_name(self):
        """ common_name.setter validates the FQDN that will be used to generate
            the CN field for the certificate. This will typically be the same value as the system_name outside of certain use cases for load balancer where the system Ottr connects to needs to generate a certificate with a CN different than the system_name.

        Returns:
            Validates FQDN, exception will be thrown if format is incorrect.
        """
        return self._common_name

    @common_name.setter
    def common_name(self, value):
        self._common_name = value
        domain = '{domain}.{suffix}'.format(domain=tldextract.extract(
            self._common_name).domain, suffix=tldextract.extract(self._common_name).suffix)
        if not isinstance(value, str):
            app.api_namespace.abort(
                500, status=f"common_name {self._common_name} required to be a string (str)", statusCode='500')
        if self._common_name != 'None':
            if not bool(tldextract.extract(self._common_name).suffix):
                app.api_namespace.abort(500, status="common_name Does Not Contain a FQDN: {}".format(
                    self._common_name), statusCode='500')
            if domain not in self.valid_domains:
                app.api_namespace.abort(500, status="common_name {} Not a Valid Domain: {}".format(
                    self._common_name, self.valid_domains), statusCode='500')
        else:
            app.api_namespace.abort(
                500, status="common_name Empty, Please Provide a FQDN.", statusCode='500')

    @property
    def ip_address(self):
        """ip_address.setter validates that your IPv4 Address (i.e. 10.0.0.1)
            is in a valid format. If an object with an invalid IP is added an
            exception will be thrown.

        Returns:
            Validates IPv4 Address, exception will be thrown if format is
            incorrect.
        """
        return self._ip_address

    @ip_address.setter
    def ip_address(self, value):
        self._ip_address = value
        if not isinstance(value, str):
            app.api_namespace.abort(
                500, status=f"ip_address {self._ip_address} required to be a string (str)", statusCode='500')
        if self._ip_address != 'None':
            result = self._ip_address.split('.')
            if len(result) != 4:
                app.api_namespace.abort(500, status="ip_address Does Not Contain Valid IPv4 Address: {}".format(
                    self._ip_address), statusCode='500')
            for octet in result:
                if not octet.isdigit():
                    app.api_namespace.abort(500, status="ip_address Does Not Contain Valid IPv4 Address: {}".format(
                        self._ip_address), statusCode='500')
                integer = int(octet)
                if integer < 0 or integer > 255:
                    app.api_namespace.abort(500, status="ip_address Does Not Contain Valid IPv4 Address: {}".format(
                        self._ip_address), statusCode='500')
        else:
            app.api_namespace.abort(
                500, status="ip_address Empty, Please Provide a IPv4 Address.", statusCode='500')

    @property
    def subject_alternative_name(self):
        """subject_alternative_name.setter validates that your Subject
            Alternative Names (SANs) are all valid Fully Qualified Domain
            Names (FQDN). Within the list if any element has an invalid
            FQDN an exception will be thrown.

        Returns:
            Validates each Subject Alternative Name, exception will be thrown
            if format is incorrect.
        """
        return self._subject_alternative_name

    @subject_alternative_name.setter
    def subject_alternative_name(self, value):
        self._subject_alternative_name = value
        if not isinstance(value, list):
            app.api_namespace.abort(
                500, status=f"subject_alternative_name {self._subject_alternative_name} required to be a list (list)", statusCode='500')
        for subject_alternative_name in self._subject_alternative_name:
            if subject_alternative_name == '*':
                app.api_namespace.abort(500, status="Subject Alternative Name (SAN) Cannot Contain '*': {}".format(
                    self._subject_alternative_name), statusCode='500')
            elif not bool(tldextract.extract(subject_alternative_name).suffix):
                app.api_namespace.abort(500, status="subject_alternative_name Does Not Contain a FQDN: {}".format(
                    subject_alternative_name), statusCode='500')
            else:
                domain = '{domain}.{suffix}'.format(domain=tldextract.extract(
                    subject_alternative_name).domain, suffix=tldextract.extract(subject_alternative_name).suffix)
                if domain not in self.valid_domains:
                    app.api_namespace.abort(500, status="subject_alternative_name {} Not a Valid Domain: {}".format(
                        subject_alternative_name, self.valid_domains), statusCode='500')

    @property
    def data_center(self):
        """data_center.setter validates that your Data Center value
            is in string (str) format, if an element is not a string an
            exception will be thrown.
        """
        return self._data_center

    @data_center.setter
    def data_center(self, value):
        self._data_center = value
        if not isinstance(value, str):
            app.api_namespace.abort(
                500, status=f"data_center {self._data_center} required to be a string (str)", statusCode='500')
    @property
    def os_version(self):
        """os_version.setter validates that your OS Version value (i.e. 1.0.0)
            is in string (str) format, if an element is not a string an
            exception will be thrown.
        """
        return self._os_version

    @os_version.setter
    def os_version(self, value):
        self._os_version = value
        if not isinstance(value, str):
            app.api_namespace.abort(
                500, status=f"os_version {self._os_version} required to be a string (str)", statusCode='500')
    @property
    def device_model(self):
        """device_model.setter validates that your Device Model value (i.e
            PA-XXXX) is in string (str) format, if an element is not a string an
            exception will be thrown.
        """
        return self._device_model

    @device_model.setter
    def device_model(self, value):
        self._device_model = value
        if not isinstance(value, str):
            app.api_namespace.abort(
                500, status=f"device_model {self._device_model} required to be a string (str)", statusCode='500')
    @property
    def origin(self):
        """device_model.setter validates that your Origin value (i.e. API)
            is in string (str) format, if an element is not a string an
            exception will be thrown.
        """
        return self._origin

    @origin.setter
    def origin(self, value):
        self._origin = value
        if not isinstance(value, str):
            app.api_namespace.abort(
                500, status=f"origin {self._origin} required to be a string (str)", statusCode='500')
