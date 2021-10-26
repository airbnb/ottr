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

import jwt
from parse import parse
from datetime import datetime, timedelta

import logging
logger = logging.getLogger(__name__)


def validate_token_header(header, public_key):
    if not header:
        logger.info('No header')
        return None

    parse_result = parse('Bearer {}', header)
    if not parse_result:
        logger.info(f'Wrong format for header "{header}"')
        return None
    token = parse_result[0]

    try:
        decoded_token = decode_token(token.encode('utf8'), public_key)
    except jwt.exceptions.DecodeError:
        logger.warning(f'Error decoding header "{header}". '
                       'This may be key missmatch or wrong key')
        return None
    except jwt.exceptions.ExpiredSignatureError:
        logger.error(f'Authentication header has expired "{header}"')
        return None

    # Check Token Expiration
    if 'exp' not in decoded_token:
        logger.warning('Token does not have expiry (exp)')
        return None

    # Check Username from JWT
    if 'username' not in decoded_token:
        logger.warning('Token does not have username')
        return None

    username = decoded_token.get('username')
    logger.info(f'{username} Authenticated Successfully')
    return decoded_token['role']


def decode_token(token, public_key):
    return jwt.decode(token, public_key, algoritms='RS256')


def encode_token(payload, private_key):
    return jwt.encode(payload, private_key, algorithm='RS256')


def generate_token_header(username, private_key):
    '''
    Generate a token header base on the username.
    Sign using the private key.
    '''
    payload = {
        'username': username,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=30),
        'role': 'ADMIN'
    }
    token = encode_token(payload, private_key).decode('utf-8')
    return f'Bearer {token}'
