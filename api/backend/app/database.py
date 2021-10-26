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
import requests
from pathlib import Path

from flask_sqlalchemy import SQLAlchemy

from backend.app.shared.client import get_secret

REGION = os.environ['AWS_DEFAULT_REGION']
DATABASE_ENGINE = os.environ['DATABASE_ENGINE']
PREFIX = os.environ['PREFIX']

POSTGRES_PASSWORD = get_secret(
    f'{PREFIX}/otter/database', 'POSTGRES_PASSWORD', REGION)


if DATABASE_ENGINE == 'SQLITE':
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    path = dir_path / '..'

    # Database initialisation
    FILE_PATH = f'{path}/db.sqlite3'
    DB_URI = 'sqlite+pysqlite:///{file_path}'
    db_config = {
        'SQLALCHEMY_DATABASE_URI': DB_URI.format(file_path=FILE_PATH),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    }

elif DATABASE_ENGINE == 'POSTGRESQL': # pragma: no cover
    db_params = {
        'host': os.environ['POSTGRES_HOST'],
        'database': os.environ['POSTGRES_DB'],
        'user': os.environ['POSTGRES_USER'],
        'pwd': POSTGRES_PASSWORD,
        'port': os.environ['POSTGRES_PORT'],
    }

    # Aurora Postgres Serverless
    DB_URI = 'postgresql://{user}:{pwd}@{host}:{port}' # pragma: no cover

    # AWS RDS Certificate
    # url = "https://truststore.pki.rds.amazonaws.com/{region}/{region}-bundle.pem".format(
    #     region=REGION)
    # r = requests.get(url, allow_redirects=True)
    # open('rds.pem', 'wb').write(r.content)

    # RDS Instance (Compute Node)
    # DB_URI = 'postgresql://{user}:{pwd}@{host}:{port}/{database}?sslmode=verify-full&sslrootcert=./rds.pem'

    # DEVELOPMENT MODE (docker-compose)
    # DB_URI = 'postgresql://{user}:{pwd}@{host}/{database}'

    db_config = {
        'SQLALCHEMY_DATABASE_URI': DB_URI.format(**db_params),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    } # pragma: no cover

else: # pragma: no cover
    raise Exception('Incorrect DATABASE_ENGINE')

db = SQLAlchemy()
