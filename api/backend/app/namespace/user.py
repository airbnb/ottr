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

import bcrypt
from datetime import datetime, timedelta

from flask_restx import Resource
from flask import request

from backend.app.database import db
from backend.app.namespace import authorization
from backend.app.shared.logger import get_logger
from backend.app.shared.client import validate_password
from backend.app.models import (User, user_namespace,
                                user_namespace, user_login,
                                user_token, user_credentials,
                                PRIVATE_KEY)

LOGGER = get_logger(__name__)


@user_namespace.route('/v1/authenticate', methods=['POST', 'PUT'])
class UsersLogin(Resource):
    @user_namespace.doc('user_login', responses={401: 'Authentication Failure'}, description='Generate Bearer Token')
    @user_namespace.response(model=user_token, code=200, description='Success')
    @user_namespace.response(200, 'Success', user_token)
    @user_namespace.expect(user_login)
    def post(self):
        json_data = request.json
        username = json_data['username']
        password = json_data['password']

        user = User.query.get(username)
        if user is None:
            return {'message': 'Authentication Failure'}, 401

        hashed_credentials = user.password
        username = user.username
        role = user.role

        try:
            if bcrypt.checkpw(password.encode('utf8'), hashed_credentials.encode('utf8')):

                payload = {
                    'username': username,
                    'role': role,
                    'iat': datetime.utcnow(),
                    'exp': datetime.utcnow() + timedelta(minutes=30),
                }

                signature = authorization.encode_token(payload, PRIVATE_KEY)
                token = signature.decode('utf8')
                return {'token': f'Bearer {token}'}

            else:
                LOGGER.info(f'{username} Authentication Failure')
                return {'message': 'Authentication Failure'}, 401

        except Exception as error:
            user_namespace.abort(
                500, error.__doc__, statusCode='500')

    @user_namespace.doc('user_login_update', responses={204: 'Success', 401: 'Authentication Failure'}, description='Update Password')
    @user_namespace.expect(user_credentials)
    def put(self):
        json_data = request.json
        username = json_data['username']
        password = json_data['password']
        updated_password = json_data['updated_password']
        encoded_password = updated_password.encode('utf8')

        # PASSWORD VALIDATION
        if not validate_password(updated_password):
            return {'Invalid Password': 'Must be at least 8 characters with a capital letter [A-Z], lowercase letter [a-z], number [0-9], and special character [@!%*#?&.].'}, 500

        user = User.query.get(username)

        if user is None:
            return {'message': 'Authentication Failure'}, 401

        hashed_credentials = user.password
        username = user.username

        try:
            if bcrypt.checkpw(password.encode('utf8'), hashed_credentials.encode('utf8')):
                password_hash = bcrypt.hashpw(
                    encoded_password, bcrypt.gensalt(14))
                user.password = password_hash.decode('utf8')
                db.session.commit()
                return '', 204
            else:
                return {'message': 'Authentication Failure'}, 401

        except Exception as error:
            user_namespace.abort(
                500, error.__doc__, statusCode='500')
