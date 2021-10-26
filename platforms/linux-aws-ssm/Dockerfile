FROM python:3.9-slim

RUN apt-get update && \
    apt-get -y install --no-install-recommends git \
    jq awscli nmap curl wget && \
    rm -rf /var/lib/apt/lists

ENV user otter
ENV HOME /home/otter
RUN useradd --create-home ${user}
USER ${user}

WORKDIR /home/${user}

COPY requirements.txt ${WORKDIR}
RUN pip3 install --no-cache-dir -r requirements.txt && \
    git clone https://github.com/acmesh-official/acme.sh.git
COPY --chown=otter:otter src ${WORKDIR}
RUN chmod -R 700 /home/otter/*.sh /home/otter/*.py

LABEL maintainer="Kenneth Yang <kenneth.yang@airbnb.com>" \
    version="1.0.0"

ENTRYPOINT ["./entrypoint.sh"]
