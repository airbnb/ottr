import logging

import pytest
from mock import patch

from otter.router.src.shared.device import Device
from otter.router.src.shared.exceptions import DeviceValidationError
from otter.router.src.shared.logger import get_logger, set_formatter, LogFormatter


class TestSystemName:
    def test_invalid_type(self):
        with pytest.raises(TypeError):
            device = Device(
                system_name=123,
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority='lets_encrypt',
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['test.example.com']
            )

    def test_unsupported_domains(self):
        with pytest.raises(DeviceValidationError):
            device = Device(
                system_name='test.invalid.com',
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority='lets_encrypt',
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['test.invalid.com']
            )

    def test_suffix_not_present(self):
        with pytest.raises(DeviceValidationError):
            device = Device(
                system_name='test.airbnb',
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority='lets_encrypt',
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['test.example.com']
            )


class TestHostname:
    def test_invalid_type(self):
        with pytest.raises(TypeError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address=123,
                certificate_authority='lets_encrypt',
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['test.example.com']
            )

    def test_invalid_ip_length(self):
        with pytest.raises(DeviceValidationError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address='10.0.1',
                certificate_authority='lets_encrypt',
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['test.example.com']
            )

    def test_invalid_ip_octet(self):
        with pytest.raises(DeviceValidationError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address='10.0.0.x',
                certificate_authority='lets_encrypt',
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['test.example.com']
            )

    def test_invalid_ip_integer(self):
        with pytest.raises(DeviceValidationError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address='10.0.0.256',
                certificate_authority='lets_encrypt',
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['test.example.com']
            )

    def test_none_value(self):
        with pytest.raises(DeviceValidationError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                certificate_authority='lets_encrypt',
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['test.example.com']
            )


class TestCertificateAuthority:
    def test_invalid_type(self):
        with pytest.raises(TypeError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority=123,
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['test.example.com']
            )

    def test_invalid_ca(self):
        with pytest.raises(DeviceValidationError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority='invalid_ca',
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['test.example.com']
            )


class TestHostPlatform:
    def test_invalid_type(self):
        with pytest.raises(TypeError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority='lets_encrypt',
                data_center='example',
                host_platform=123,
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['test.example.com']
            )

    def test_invalid_platform(self):
        with pytest.raises(DeviceValidationError):
            device = Device(
                system_name='test.example.com', ip_address='10.0.0.1', certificate_authority='lets_encrypt', data_center='example', host_platform='invalid_platform', os_version='1.0.0', device_model='PA-XXXX', origin='API', subject_alternative_name=['test.example.com'])


class TestSubjectAlternativeName:
    def test_invalid_type(self):
        with pytest.raises(TypeError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority='lets_encrypt',
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name='example.com'
            )

    def test_wildcard_san(self):
        with pytest.raises(DeviceValidationError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority='lets_encrypt',
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['example.com', '*']
            )

    def test_invalid_domain(self):
        with pytest.raises(DeviceValidationError):
            device = Device(
                system_name='test.invalid.com',
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority='lets_encrypt',
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['invalid.com']
            )

    def test_subject_alternative_name_none(self):
        device = Device(
            system_name='test.example.com',
            common_name='test.example.com',
            ip_address='10.0.0.1',
            certificate_authority='lets_encrypt',
            data_center='example',
            host_platform='panos',
            os_version='1.0.0',
            device_model='PA-XXXX',
            origin='API',
        )
        assert device.subject_alternative_name == ['test.example.com']

    def test_subject_alternative_name_inalid_sans(self):
        with pytest.raises(DeviceValidationError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority='lets_encrypt',
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['example.invalid.com']
            )

    def test_invalid_domain_suffix(self):
        with pytest.raises(DeviceValidationError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority='lets_encrypt',
                data_center='example',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['example']
            )


class TestValidDevice:
    device = Device(
        system_name='test.example.com',
        common_name='test.example.com',
        ip_address='10.0.0.1',
        certificate_authority='lets_encrypt',
        data_center='example',
        host_platform='panos',
        os_version='1.0.0',
        device_model='PA-XXXX',
        origin='API',
        subject_alternative_name=['example.com']
    )

    def test_valid_system_name(self):
        assert TestValidDevice.device.system_name == 'test.example.com'

    def test_valid_hostname(self):
        assert TestValidDevice.device.ip_address == '10.0.0.1'

    def test_str_method(self):
        output = "{ip_address: 10.0.0.1, system_name: test.example.com, common_name: test.example.com, host_platform: panos, os_version: 1.0.0, device_model: PA-XXXX, certificate_authority: lets_encrypt, data_center: example, subject_alternative_name: ['example.com'], validate_certificate: True}"
        assert str(TestValidDevice.device) == output


class TestDeviceTypeError:
    def test_data_center_type(self):
        with pytest.raises(TypeError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority='lets_encrypt',
                data_center=['dc1', 'dc2'],
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['example.com']
            )

    def test_os_version_type(self):
        with pytest.raises(TypeError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority='lets_encrypt',
                data_center='dc1',
                host_platform='panos',
                os_version=1.0,
                device_model='PA-XXXX',
                origin='API',
                subject_alternative_name=['example.com']
            )

    def test_device_model_type(self):
        with pytest.raises(TypeError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority='lets_encrypt',
                data_center='dc1',
                host_platform='panos',
                os_version='1.0.0',
                device_model=['PA-XXXX'],
                origin='API',
                subject_alternative_name=['example.com']
            )

    def test_origin_type(self):
        with pytest.raises(TypeError):
            device = Device(
                system_name='test.example.com',
                common_name='test.example.com',
                ip_address='10.0.0.1',
                certificate_authority='lets_encrypt',
                data_center='dc1',
                host_platform='panos',
                os_version='1.0.0',
                device_model='PA-XXXX',
                origin=['API'],
                subject_alternative_name=['example.com']
            )


class TestLogger:
    def test_get_logger(self):
        logger_name = 'pytest'
        logger = get_logger(logger_name)
        assert logger.name == logger_name

    def test_get_logger_env_level(self, monkeypatch):
        level = 'DEBUG'
        monkeypatch.setenv('LOGGER_LEVEL', level)
        logger = get_logger('test')
        assert logging.getLevelName((logger.getEffectiveLevel())) == level

    def test_get_logger_user_level(self):
        level = 'CRITICAL'
        logger = get_logger('test', level)
        assert logging.getLevelName((logger.getEffectiveLevel())) == level

    @patch('logging.Logger.error')
    def test_get_logger_bad_level(self, log_mock):
        logger = get_logger('test', 'foo')
        assert logging.getLevelName(logger.getEffectiveLevel()) == 'INFO'
        log_mock.assert_called_with(
            'Defaulting to INFO logging: %s', 'Unknown level: \'FOO\'')

    def test_set_logger_formatter_existing_handler(self):
        logger = logging.getLogger('test')
        handler = logging.StreamHandler()
        logger.addHandler(handler)
        set_formatter(logger)
        assert type(handler.formatter) == type(LogFormatter())

    @patch('logging.Logger.hasHandlers')
    def test_set_logger_formatter_new_handler(self, log_mock):
        logger = logging.getLogger('test')
        log_mock.return_value = False
        set_formatter(logger)
        assert type(logger.handlers[0].formatter) == type(LogFormatter())
