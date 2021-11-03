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

import requests
import json

from .logger import get_logger

LOGGER = get_logger(__name__)

# Generic Exception Error Handling


class generic_exception(object):
    def __init__(self, message):
        self.message = message

    def __call__(self, func):
        def wrapper(*args):
            try:
                response: requests.models.Response = func(*args)
                LOGGER.info(response.content)
            except Exception:
                LOGGER.error(self.message)
                raise ValueError
        return wrapper

# HTTP Request Error Handling

def http_exception(func):
    def wrapper(*args, **kwargs):
        resp: requests.models.Response = func(*args, **kwargs)
        if resp.status_code != 200:
            raise RuntimeError(**json.loads(resp._content))
        else:
            return resp

    return wrapper
