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

from flask import Flask
from flask_restx import Api


def create_app():
    from backend.app.namespace.admin import admin_namespace
    from backend.app.namespace.api import api_namespace
    from backend.app.namespace.user import user_namespace

    application = Flask(__name__)
    application.config.SWAGGER_UI_DOC_EXPANSION = 'list'

    api = Api(application, version='1.0', title='Ottr Public Key Infrastructure',
              description='Ottr API for Device Certificate Rotation')

    from backend.app.database import db, db_config

    application.config['RESTPLUS_MASK_SWAGGER'] = False
    application.config.update(db_config)
    db.init_app(application)
    application.db = db

    with application.app_context():
        db.create_all()

    api.add_namespace(admin_namespace)
    api.add_namespace(api_namespace)
    api.add_namespace(user_namespace)

    return application
