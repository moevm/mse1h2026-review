FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
RUN pip install --no-cache-dir pytest pytest-asyncio httpx==0.24.1 starlette==0.36.3

COPY backend /app/backend
COPY tests /app/tests

ENV PYTHONPATH=/app/backend

CMD ["python3", "-m", "pytest", "tests/test_functional.py", "tests/test_integration.py", "-W", "ignore::DeprecationWarning", "-v"]
