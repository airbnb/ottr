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

import logging
import os

LOCAL_LOGGER_FMT = '[%(levelname)s %(asctime)s (%(name)s:%(lineno)d)]: %(message)s'

logging.basicConfig(level=logging.INFO, format=LOCAL_LOGGER_FMT)


class LogFormatter(logging.Formatter):

    def formatException(self, ei):
        value = super().formatException(ei)
        return value.replace('\n', '\r')


def set_formatter(logger):
    if not logger.hasHandlers():
        return

    for handler in logger.handlers + logger.parent.handlers:
        fmt = handler.formatter._fmt if handler.formatter else None
        handler.setFormatter(LogFormatter(fmt=fmt))


def get_logger(name, level=None):
    if not level:
        level = os.environ.get('LOGGER_LEVEL', 'INFO')

    logger = logging.getLogger(name)
    set_formatter(logger)

    try:
        logger.setLevel(level.upper())
    except (TypeError, ValueError) as err:
        logger.setLevel('INFO')
        logger.error('Defaulting to INFO logging: %s', str(err))

    return logger
