#!/bin/bash

AWS_REGION=us-east-1 DYNAMODB_TABLE=otter-example pytest --cov-report html --cov=. tests/unit acme/tests -s -v

# # API Tests
# AWS_ACCOUNT=123456789012 AWS_DEFAULT_REGION=us-east-1 TABLE=ottr-example
# DATABASE_ENGINE=SQLITE PREFIX=test POSTGRES_HOST=db POSTGRES_DB=otter
# POSTGRES_USER=postgres POSTGRES_PORT=5432 pytest --cov-report html --cov=.
# api/backend/tests -s -v --disable-pytest-warnings


# Remove SQLITE Database Data
rm api/backend/db.sqlite3