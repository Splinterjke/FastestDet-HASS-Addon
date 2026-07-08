FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir onnxruntime opencv-python-headless requests paho-mqtt==1.6.1 numpy

RUN apt-get update && apt-get install -y --no-install-recommends wget && \
    mkdir -p /models && \
    wget -O /models/FastestDetV2.onnx https://github.com/Pairman/FastestDetV2/releases/download/v1/fastestdetv2.onnx && \
    apt-get purge -y wget && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

CMD ["python", "ha_person_detector.py"]