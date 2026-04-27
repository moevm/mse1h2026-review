import os
import pytest
import httpx
import psycopg2
import pika

DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/app_db")

RABBIT_USER = os.getenv("RABBIT_USER", "rabbit_user")
RABBIT_PASS = os.getenv("RABBIT_PASS", "secure_password_mq")
RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")

API_URL = os.getenv("API_URL", "http://backend:8000")

@pytest.mark.asyncio
async def test_api_health():
    try:
        async with httpx.AsyncClient(base_url=API_URL, timeout=10.0) as ac:
            response = await ac.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    except Exception as e:
        pytest.fail(f"Бэкенд недоступен по адресу {API_URL}: {e}")

def test_db_connection():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute('SELECT 1')
        assert cur.fetchone()[0] == 1
        cur.close()
        conn.close()
    except Exception as e:
        pytest.fail(f"Ошибка подключения к базе: {e}")

def test_rabbit_connection():
    try:
        credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
        parameters = pika.ConnectionParameters(
            host=RABBIT_HOST, 
            credentials=credentials,
            connection_attempts=3,
            retry_delay=5
        )
        connection = pika.BlockingConnection(parameters)
        assert connection.is_open
        connection.close()
    except Exception as e:
        pytest.fail(f"RabbitMQ недоступен по адресу {RABBIT_HOST}: {e}")
