import logging

from mock import patch
from acme.acme.logger import get_logger, set_formatter, LogFormatter


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
