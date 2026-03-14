import os
import pika

def callback(ch, method, properties, body):
    print("Hello world from consumer!")
    print("Received message:", body.decode(), flush=True)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    queue_name = os.getenv("QUEUE_NAME", "ai-review")
    rabbit_user = os.getenv("RABBIT_USER", "guest")
    rabbit_pass = os.getenv("RABBIT_PASS", "guest")
    
    credentials = pika.PlainCredentials(rabbit_user, rabbit_pass)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbitmq_host,
            credentials=credentials
        )
    )
    
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback
    )
    
    print(f"Consumer started. Waiting for messages on {queue_name}...", flush=True)
    channel.start_consuming()

if __name__ == "__main__":
    main()
