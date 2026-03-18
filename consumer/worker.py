import os
import pika
import json
from ai_review_runner import run_ai_review_for_pr

def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        print(f"Received message: {message}", flush=True)
        run_ai_review_for_pr(
            repo_url=message["repo_url"],
            repo_name=message["repo_name"],
            repo_owner=message["repo_owner"],
            pr_number=message["pr_number"],
            branch=message["branch"]
        )
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing message: {e}", flush=True)

def main():
    queue_name = os.getenv("QUEUE_NAME", "webhook_queue")
    rabbitmq_url = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672/")
    
    params = pika.URLParameters(rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    print(f"Consumer started. Waiting for messages on {queue_name}...", flush=True)
    channel.start_consuming()

if __name__ == "__main__":
    main()
