#!/bin/bash
echo 'Stop grafecully postgres'
su-exec postgres pg_ctl stop -m smart

postgres_down () {
    pg_isready -U postgres
    if [ $? -eq 2 ]; then
        # DB not available
        return 0
    else
        return 1
    fi
}

until postgres_down; do
  >&2 echo "Postgres is still available - sleeping"
  sleep 1
done
