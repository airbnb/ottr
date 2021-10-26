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
import datetime

import bcrypt
from sqlalchemy import func
from flask_restx import Namespace, fields

from backend import app
from backend.app.shared import client


class User(app.db.Model):
    username = app.db.Column(app.db.VARCHAR(
        255), primary_key=True, nullable=False)
    password = app.db.Column(app.db.VARCHAR(255), nullable=False)
    role = app.db.Column(app.db.VARCHAR(255), nullable=False)
    timestamp = app.db.Column(app.db.DateTime, server_default=func.now())

    def __init__(self, username, password, role):
        self.username = username
        password_hash = bcrypt.hashpw(
            password.encode('utf8'), bcrypt.gensalt(14))
        # Decode Hash to Prevent Encoding Twice (POSTGRESQL Encodes By Default)
        self.password = password_hash.decode('utf8')
        self.registered_on = datetime.datetime.now()
        self.role = role


REGION = os.environ['AWS_DEFAULT_REGION']
PREFIX = os.environ['PREFIX']
# SM_CLIENT = SecretsManager(REGION)
PRIVATE_KEY = client.get_secret(f'{PREFIX}/otter/private_key', region=REGION)
PUBLIC_KEY = client.get_secret(f'{PREFIX}/otter/public_key', region=REGION)

rbac = ['ADMIN', 'DEVELOPER', 'PRIVILEGED']
admin_permissions = ['ADMIN']
privileged_permissions = ['ADMIN', 'PRIVILEGED']
developer_permissions = ['ADMIN', 'PRIVILEGED', 'DEVELOPER']

# ADMIN: Create Users/Delete Users/List Users
# PRIVILEGED: Delete Assets/Create Assets/Update Assets
# DEVELOPER: Get Assets/Rotate Certificate

# Admin Namespace
admin_namespace = Namespace('admin', description='Admin Operations')

# Authentication Parser
authentication_parser = admin_namespace.parser()

authentication_parser.add_argument(
    'Authorization', location='headers', required=True, type=str, help='Bearer Access Token')

# Database Object
user_model = admin_namespace.model(
    'user_object', {
        'username': fields.String(),
        'role': fields.String(),
        'timestamp': fields.DateTime()
    }
)


# Login Response
user_token = admin_namespace.model(
    'token', {
        'token': fields.String(description='JSON Web Token')
    }
)

# User Creation Object
create_user = admin_namespace.model(
    'create_user',
    {
        'username': fields.String(description='Username', required=True),
        'password': fields.String(description='Password', required=True),
        'role': fields.String(description='[ADMIN, DEVELOPER, PRIVILEGED]', required=True)
    }
)


# API Namespace
api_namespace = Namespace('api', description='API Operations')

# Asset Object
asset_output = api_namespace.model(
    'asset_object', {
        'system_name': fields.String(),
        'common_name': fields.String(),
        'certificate_authority': fields.String(),
        'certificate_expiration': fields.String(),
        'data_center': fields.String(),
        'device_model': fields.String(),
        'host_platform': fields.String(),
        'ip_address': fields.String(),
        'os_version': fields.String(),
        'origin': fields.String(),
        'subject_alternative_name': fields.List(fields.String())
    }
)

asset_input = api_namespace.model(
    'asset_input', {
        'system_name': fields.String(),
        'common_name': fields.String(),
        'certificate_authority': fields.String(),
        'data_center': fields.String(),
        'device_model': fields.String(),
        'host_platform': fields.String(),
        'ip_address': fields.String(),
        'os_version': fields.String(),
        'subject_alternative_name': fields.List(fields.String()),
    }
)

# User Namespace
user_namespace = Namespace('user', description='User Operations')

# User Login Body
user_login = admin_namespace.model(
    'user_login', {
        'username': fields.String(description='Username', required=True),
        'password': fields.String(description='User Password', required=True),
    }
)
# User Update Password
user_credentials = admin_namespace.model(
    'user_credentials',
    {
        'username': fields.String(description='Username', required=True),
        'password': fields.String(description='Current User Password', required=True),
        'updated_password': fields.String(description='Updated User Password', required=True)
    }
)
