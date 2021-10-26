FROM alpine:3.9

ENV PYTHONPATH "${PYTHONPATH}:/opt/code/"

ARG POSTGRES_DB
ENV POSTGRES_DB $POSTGRES_DB
ARG POSTGRES_USER
ENV POSTGRES_USER $POSTGRES_USER
ARG POSTGRES_PASSWORD
ENV POSTGRES_PASSWORD $POSTGRES_PASSWORD
ARG POSTGRES_PORT
ARG AWS_DEFAULT_REGION
ENV AWS_DEFAULT_REGION $AWS_DEFAULT_REGION
ARG TABLE
ENV TABLE $TABLE
ARG PREFIX
ENV PREFIX $PREFIX

# Development Environment
# ARG AWS_ACCESS_KEY_ID
# ENV AWS_ACCESS_KEY_ID $AWS_ACCESS_KEY_ID
# ARG AWS_SECRET_ACCESS_KEY
# ENV AWS_SECRET_ACCESS_KEY $AWS_SECRET_ACCESS_KEY
# ARG AWS_SESSION_TOKEN
# ENV AWS_SESSION_TOKEN $AWS_SESSION_TOKEN

ENV LANG en_US.utf8
EXPOSE $POSTGRES_PORT

ENV POSTGRES_HOST localhost
ENV DATABASE_ENGINE POSTGRESQL

# Store Data Inside Container (Persistent Storage)
ENV PGDATA /var/lib/postgresql/data

RUN apk update
RUN apk add bash curl su-exec python3
RUN apk add postgresql postgresql-contrib postgresql-dev
RUN apk add python3-dev build-base linux-headers gcc libffi-dev

# Adding Code
WORKDIR /opt/code

RUN mkdir -p /opt/code/db
# Add POSTGRESQL Setup
ADD ./docker/db/postgres_setup.sh /opt/code/db/
RUN  /opt/code/db/postgres_setup.sh

## Install Code and Prepare DB
ADD ./backend/requirements.txt /opt/code

RUN pip3 install -r requirements.txt

## Import Code, Initialize the DB
ADD ./backend/ /opt/code/backend
ADD ./docker/db/* /opt/code/db/

## Prepare DB
RUN /opt/code/db/prepare_db.sh

# Start DB
USER postgres
CMD ["postgres"]
