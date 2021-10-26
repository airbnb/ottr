########
# Image to Compile Dependencies
########
FROM alpine:3.9 AS compile-image

# Add Requirements
RUN apk add --update python3

RUN mkdir -p /opt/code
WORKDIR /opt/code

# Install Dependencies
RUN apk add python3-dev build-base gcc linux-headers postgresql-dev libffi-dev

# Create Virtual Environment for Python Dependencies
RUN python3 -m venv /opt/venv

# Set Path for Virtual Environment
ENV PATH="/opt/venv/bin:$PATH"
RUN pip3 install --upgrade pip

# Install and Compile uwsgi
RUN pip3 install uwsgi==2.0.18
# Install Dependencies
COPY backend/requirements.txt /opt/
RUN pip3 install -r /opt/requirements.txt

########
# Runtime Image
########
FROM alpine:3.9 AS runtime-image

# Install Python
RUN apk add --update python3 curl libffi postgresql-libs

# Copy uWSGI Configuration
RUN mkdir -p /opt/uwsgi
ADD docker/app/uwsgi.ini /opt/uwsgi/
ADD docker/app/start_server.sh /opt/uwsgi/

# Create Service User
RUN addgroup -S uwsgi
RUN adduser -H -D -S uwsgi
USER uwsgi

# Copy Virtual Environment with Compiled Dependencies
COPY --chown=uwsgi:uwsgi --from=compile-image /opt/venv /opt/venv
# Activate Virtual Environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy Code
ENV PYTHONPATH "${PYTHONPATH}:/opt/code/"
COPY --chown=uwsgi:uwsgi backend/ /opt/code/backend

ARG POSTGRES_DB
ENV POSTGRES_DB $POSTGRES_DB
ARG DATABASE_ENGINE
ENV DATABASE_ENGINE $DATABASE_ENGINE
ARG POSTGRES_USER
ENV POSTGRES_USER $POSTGRES_USER
ARG POSTGRES_PORT
ENV POSTGRES_PORT $POSTGRES_PORT
ARG POSTGRES_HOST
ENV POSTGRES_HOST $POSTGRES_HOST
ARG AWS_DEFAULT_REGION
ENV AWS_DEFAULT_REGION $AWS_DEFAULT_REGION
ARG AWS_ACCOUNT
ENV AWS_ACCOUNT $AWS_ACCOUNT

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
# ARG POSTGRES_PASSWORD
# ENV POSTGRES_PASSWORD $POSTGRES_PASSWORD

# Execute
WORKDIR /opt/code
EXPOSE 8000
CMD ["/bin/sh", "/opt/uwsgi/start_server.sh"]
