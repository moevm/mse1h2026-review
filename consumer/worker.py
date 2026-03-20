import os
import pika
import json
import requests
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
        
        comment_body = message.get("comment", {}).get("body", "")
        if comment_body.strip() != "/ai-review":
            print(f"Ignoring comment: '{comment_body}'", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        pr_number = message.get("issue", {}).get("number")
        repo_full_name = message.get("repository", {}).get("full_name")
        repo_url = message.get("repository", {}).get("html_url")
        token = os.getenv("GITHUB_TOKEN")
        branch = get_branch(repo_full_name, pr_number, token)
        if not branch:
            print(f"Branch not found for PR #{pr_number}", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        missing_fields = []
        if not pr_number:
            missing_fields.append("pr_number")
        if not repo_full_name:
            missing_fields.append("repo_full_name")
        if not repo_url:
            missing_fields.append("repo_url")
        if missing_fields:
            print(f"Missing fields: {', '.join(missing_fields)}", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        repo_owner, repo_name = repo_full_name.split("/")
        
        print(f"Processing PR #{pr_number} in {repo_full_name}, branch: {branch}", flush=True)
        
        run_ai_review_for_pr(
            repo_url=repo_url,
            repo_name=repo_name,
            repo_owner=repo_owner,
            pr_number=pr_number,
            branch=branch
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
