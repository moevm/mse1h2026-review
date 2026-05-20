FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

COPY consumer/requirements.txt .
COPY config /app/config

RUN pip install --no-cache-dir -r requirements.txt

COPY consumer/app/ .

CMD ["python3", "worker.py"]
