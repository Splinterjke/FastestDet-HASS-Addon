FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir opencv-python-headless numpy requests paho-mqtt==1.6.1

RUN pip install --no-cache-dir ncnn --no-deps

RUN apt-get update && apt-get install -y --no-install-recommends wget && \
    mkdir -p /models && \
    wget -O /models/fastestdetv2.param https://github.com/Pairman/FastestDetV2/releases/download/v1/fastestdetv2.param && \
    wget -O /models/fastestdetv2.bin https://github.com/Pairman/FastestDetV2/releases/download/v1/fastestdetv2.bin && \
    apt-get purge -y wget && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

CMD ["python", "ha_person_detector.py"]