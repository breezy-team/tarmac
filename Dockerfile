FROM debian:sid-slim

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends brz python3-setuptools ca-certificates python3-httplib2 python3-launchpadlib python3-paramiko openssh-client

COPY . /tmp/tarmac

RUN cd /tmp/tarmac && python3 setup.py install && rm -rf /tmp/tarmac

ENV TARMAC_CONFIG_HOME=/config
VOLUME /config

ENV TARMAC_CACHE_HOME=/cache
VOLUME /cache

ENV TARMAC_PLUGIN_PATH=/plugins
VOLUME /plugins

ENTRYPOINT ["tarmac"]
