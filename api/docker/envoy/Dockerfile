FROM envoyproxy/envoy-dev:latest

RUN apt-get update && apt-get -q install -y \
    curl

ADD docker/envoy/start_envoy.sh /start_envoy.sh
ADD docker/envoy/envoy.yaml /etc/envoy.yaml

RUN chmod +x /start_envoy.sh

ENTRYPOINT ["/bin/sh"]

EXPOSE 8443

CMD ["start_envoy.sh"]

