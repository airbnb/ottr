#!/bin/sh
set -e

/opt/code/db/start_postgres.sh

echo 'Creating Schema'
python3 /opt/code/backend/init_db.py

/opt/code/db/stop_postgres.sh
