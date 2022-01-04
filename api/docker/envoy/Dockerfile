FROM envoyproxy/envoy:v1.19.1
RUN apt-get update && apt-get -q install -y \
    curl

ADD docker/envoy/start_envoy.sh /start_envoy.sh
ADD docker/envoy/envoy.yaml /etc/envoy.yaml

RUN chmod +x /start_envoy.sh

ENTRYPOINT ["/bin/sh"]

EXPOSE 8443

CMD ["start_envoy.sh"]

