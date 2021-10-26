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

from flask import abort, request
from backend.app.shared.client import validate_password
from flask_restx import Resource

from backend import app
from backend.app.namespace.authorization import validate_token_header
from backend.app.models import (User, admin_namespace, user_model, create_user,
                                authentication_parser, admin_permissions, developer_permissions, PUBLIC_KEY)

# ADMIN: Create Users/Delete Users/List Users
# PRIVILEGED: Delete Assets/Create Assets/Update Assets
# DEVELOPER: Get Assets/Rotate Certificate

# http://localhost:5000/?docExpansion=list


def authentication_header_parser(value, secret):
    data = validate_token_header(value, secret)
    if data is None:
        abort(401)
    return data


@admin_namespace.route('/v1/users', methods=['GET', 'POST'])
class Users(Resource):
    @admin_namespace.doc('create_user', responses={500: 'Invalid Role'}, description='Create User for API')
    @admin_namespace.response(model=user_model, code=201, description='Success')
    @admin_namespace.expect(create_user, authentication_parser)
    def post(self):
        args = authentication_parser.parse_args()
        role = authentication_header_parser(
            args['Authorization'], PUBLIC_KEY)

        try:
            if role in admin_permissions:
                json_data = request.json
                username = json_data['username']
                password = json_data['password']
                role = json_data['role']

                # PASSWORD VALIDATION
                if not validate_password(password):
                    return {'Invalid Password': 'Must be at least 8 characters with a capital letter [A-Z], lowercase letter [a-z], number [0-9], and special character [@!%*#?&.].'}, 500

                # ROLE VALIDATION
                if role not in developer_permissions:
                    return {'Invalid Role': '{} Role Invalid. Valid Roles: {}'.
                            format(role, developer_permissions)}, 500

                new_user = User(username=username,
                                password=password,
                                role=role)
                existing_user = (User
                         .query
                         .get(username))
                if not existing_user:
                    app.db.session.add(new_user)
                    app.db.session.commit()
                else:
                    return {'Invalid Request': 'User Exists'}, 500
                result = admin_namespace.marshal(new_user, user_model)
                return result, 201
            else:
                return {'Invalid Permissions': '{} Role Invalid'.format(role)}, 500

        except Exception as error:
            admin_namespace.abort(
                500, error.__doc__, statusCode='500')

    @ admin_namespace.doc('list_users', responses={500: 'Invalid Role'}, description='List Users from Database')
    @ admin_namespace.response(model=user_model, code=200, description='Success', as_list=True)
    @ admin_namespace.expect(authentication_parser)
    def get(self):
        args = authentication_parser.parse_args()
        role = authentication_header_parser(
            args['Authorization'], PUBLIC_KEY)

        try:
            if role in admin_permissions:
                users = (User
                         .query
                         .order_by('username')
                         .all())
                return admin_namespace.marshal(users, user_model)
            else:
                return {'Invalid Permissions': '{} Role Invalid'.format(role)}, 500

        except Exception as error:
            admin_namespace.abort(
                500, error.__doc__, statusCode='500')


@ admin_namespace.route('/v1/users/<string:username>', methods=['DELETE'])
class UsersDelete(Resource):
    @ admin_namespace.expect(authentication_parser)
    @ admin_namespace.doc('delete_user', responses={204: 'Success', 500: 'Invalid Role'}, description='Delete User from Database')
    def delete(self, username):
        args = authentication_parser.parse_args()
        role = authentication_header_parser(
            args['Authorization'], PUBLIC_KEY)

        # Check if User Present in Database
        try:
            if role in admin_permissions:
                user = User.query.get(username)
                if not user:
                    # No Response/Prevent Mapping of Users
                    return '', 204

                app.db.session.delete(user)
                app.db.session.commit()

                return '', 204

            else:
                return {'Invalid Permissions': '{} Role Invalid'.format(role)}, 500

        except Exception as error:
            admin_namespace.abort(
                500, error.__doc__, statusCode='500')

