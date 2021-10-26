#!/bin/bash
set -e

# Start gracefully postgres
su-exec postgres pg_ctl start

echo "Waiting till up"

until pg_isready -U postgres; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
