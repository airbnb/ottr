#!/bin/sh

mkdir -p /etc/ssl

echo "Creating a X509 certificate for $DNS_NAME"

openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/envoy.key -out /etc/ssl/envoy.crt -subj "/CN=$DNS_NAME"

/usr/local/bin/envoy -c /etc/envoy.yaml