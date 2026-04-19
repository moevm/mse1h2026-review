import os
import pika
import json
import requests
import time
from ai_review_runner import run_ai_review_for_pr

def get_branch(repo, pr, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr}"
    headers = {"Authorization": f"token {token}"} if token else {}
    
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()["head"]["ref"]
    return None

def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        print(f"Received message: {message}", flush=True)

        comment_body = message.get("comment", {}).get("body", "").strip()

        is_review = comment_body == "/ai-review"
        is_feedback = comment_body.startswith("/ai-feedback")

        if not (is_review or is_feedback):
            print(f"Ignoring comment: '{comment_body}'", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        pr_number = message.get("issue", {}).get("number")
        repo_full_name = message.get("repository", {}).get("full_name")
        repo_url = message.get("repository", {}).get("html_url")
        
        if not (pr_number and repo_full_name):
            print("Missing core fields, skipping.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        repo_owner, repo_name = repo_full_name.split("/")

        if is_feedback:
            parts = comment_body.split()
            if len(parts) >= 2:
                liked = parts[1].lower() == "like"
                backend_url = f"http://backend:8000/worker/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/feedback?liked={str(liked).lower()}"
                requests.post(backend_url)
                print(f"Feedback sent: {liked}")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if is_review:
            token = os.getenv("GITHUB_TOKEN")
            branch = get_branch(repo_full_name, pr_number, token)
            
            if not branch:
                print(f"Branch not found for PR #{pr_number}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            run_ai_review_for_pr(
                repo_url=repo_url,
                repo_name=repo_name,
                repo_owner=repo_owner,
                pr_number=pr_number,
                branch=branch
            )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Error: {e}", flush=True)
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    queue_name = os.getenv("QUEUE_NAME", "webhook_queue")
    rabbitmq_url = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672/")
    
    params = pika.URLParameters(rabbitmq_url)
    params.heartbeat = 300
    while True:
        try:
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(queue=queue_name, on_message_callback=callback)
            print(f"Consumer started. Waiting for messages on {queue_name}...", flush=True)
            try:
                channel.start_consuming()
            except (pika.exceptions.StreamLostError, ConnectionResetError):
                print("Stream lost, reconnecting...", flush=True)
                connection.close()
                time.sleep(5)

        except pika.exceptions.AMQPConnectionError as e:
            print(f"AMQP connection error: {e}, retrying...", flush=True)
            time.sleep(5)
            
if __name__ == "__main__":
    main()
