# tools.Dockerfile — prebuilt "tools" layer for the upstream functional-test compose fixture.
# Mirrors the `tools` stage of legacy/functional-test/src/test/resources/docker/compose/oss/Dockerfile (netcat,
# sshpass, python3-pip, iputils-ping, ansible 9.6.1) so that `TEST_OSS_TOOLS_IMAGE=<this image>` lets the fixture
# skip the network-heavy stage. Why a copy: in the cloud environment every outbound TLS connection is intercepted by
# the sandbox proxy with its own CA, which pip does not trust; this file can bake an extra CA (build-arg EXTRA_CA, a
# file in the build context) — the upstream Dockerfile cannot be edited (MISSION §8). Built by scripts/oracle/build-tools-image.sh.
ARG IMAGE=rundeck/rundeck:6.3.0
FROM ${IMAGE} AS tools
USER root
ARG EXTRA_CA=extra-ca.crt
COPY ${EXTRA_CA} /usr/local/share/ca-certificates/extra-ca.crt
RUN if [ -s /usr/local/share/ca-certificates/extra-ca.crt ]; then update-ca-certificates; else rm -f /usr/local/share/ca-certificates/extra-ca.crt; fi
ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
RUN apt-get update && \
    apt-get install -y netcat && \
    apt-get -y install sshpass
RUN apt-get update && \
    apt-get -y install python3-pip && \
    apt-get -y install iputils-ping && \
    pip3 install --upgrade pip
RUN pip3 install ansible==9.6.1
USER rundeck
