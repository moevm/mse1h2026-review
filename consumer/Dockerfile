FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && echo "some_text"

COPY . .

CMD ["python3", "worker.py"]
