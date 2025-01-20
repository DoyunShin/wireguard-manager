FROM python:3.12-slim

RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y --no-install-recommends wireguard-tools iptables iproute2 && \
    mkdir /app

WORKDIR /app
COPY requirements.txt ./

RUN pip install -U pip wheel setuptools && \
    pip install -U -r requirements.txt && \
    mkdir /app/data

COPY . .

EXPOSE 5000
EXPOSE 51820/udp

CMD ["python", "app.py"]
