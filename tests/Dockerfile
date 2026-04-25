FROM python:3.12-alpine

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
        pytest \
        pytest-asyncio \
        httpx \
        pika \
        psycopg2-binary

COPY . /app
