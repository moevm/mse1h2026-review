import json
import os
import time

import pika
import requests
import structlog
from ai_review_runner import run_ai_review_for_pr
from logger import setup_logger

setup_logger()
logger = structlog.get_logger()


def get_branch(repo, pr, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr}"
    headers = {"Authorization": f"token {token}"} if token else {}

    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()["head"]["ref"]
    return None


def callback(ch, method, properties, body):
    log = logger.new()
    try:
        message = json.loads(body)
        repo_full_name = message.get("repository", {}).get("full_name")
        pr_number = message.get("issue", {}).get("number")

        log = log.bind(repo=repo_full_name, pr=pr_number)
        log.info("received_message")

        comment_body = message.get("comment", {}).get("body", "")
        if comment_body.strip() != "/ai-review":
            log.info("ignoring_comment", reason="wrong_command")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if not message.get("issue", {}).get("pull_request"):
            log.info("ignoring_comment", reason="not_a_pr")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        token = os.getenv("GITHUB_TOKEN")
        branch = get_branch(repo_full_name, pr_number, token)
        if not branch:
            log.error("branch_not_found")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        repo_url = message.get("repository", {}).get("html_url")
        repo_owner, repo_name = repo_full_name.split("/")

        log.info("processing_started", branch=branch)

        run_ai_review_for_pr(
            repo_url=repo_url, repo_name=repo_name, repo_owner=repo_owner, pr_number=pr_number, branch=branch
        )

        log.info("processing_finished")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        log.error("processing_failed", error=str(e))
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

            logger.info("consumer_started", queue=queue_name, rabbit_url=rabbitmq_url)

            try:
                channel.start_consuming()
            except (pika.exceptions.StreamLostError, ConnectionResetError) as e:
                logger.warning("stream_lost", error=str(e), action="reconnecting")
                connection.close()
                time.sleep(5)

        except pika.exceptions.AMQPConnectionError as e:
            logger.error("amqp_connection_error", error=str(e), retry_in=5)
            time.sleep(5)


if __name__ == "__main__":
    main()
