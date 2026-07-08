FROM python:3.10-slim

ARG BUILD_VERSION="1.0.2"
ARG BUILD_ARCH="aarch64"

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="addon" \
  io.hass.arch="${BUILD_ARCH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir onnxruntime opencv-python-headless numpy requests paho-mqtt==1.6.1

COPY models/ /models/

COPY run.sh /run.sh
COPY ha_person_detector.py /app/ha_person_detector.py
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]