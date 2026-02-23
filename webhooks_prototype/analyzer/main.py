import os
import json
import sys
import pika
import time
import requests
import yaml
from typing import Dict, Any, Optional
from github import Github, Auth

# Читаем переменные окружения
RABBIT_URL = os.getenv("RABBIT_URL")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")

def log(msg: str) -> None:
    print(msg, flush=True)

def load_config() -> Dict[str, Any]:
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        log(f"[!] Ошибка загрузки конфига: {e}")
        return {
            "ai_review": {
                "model": "qwen2.5-coder:1.5b",
                "max_diff_length": 5000,
                "system_prompt": "Проведи code review:",
                "footer_message": "### AI Review\n\n"
            }
        }

CONFIG = load_config()

def get_ai_review(diff_text: str) -> str:
    conf = CONFIG['ai_review']
    log(f"[*] Sending to Ollama. Model: {conf['model']}")
    
    max_len = conf.get('max_diff_length', 5000)
    truncated_diff = diff_text[:max_len]

    prompt = f"{conf['system_prompt']}\n\nКод изменений:\n{truncated_diff}"

    payload = {
        "model": conf['model'],
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "AI failed to generate a response.")
    except Exception as e:
        return f"❌ Ошибка при обращении к ИИ: {e}"

def process(ch, method, properties, body) -> None:
    try:
        data = json.loads(body)
        repo_name = data['repository']['full_name']
        pr_number = data['issue']['number']
        
        log(f"\n{'-'*30}\n[*] Task received: {repo_name} #{pr_number}")

        auth = Auth.Token(GITHUB_TOKEN)
        g = Github(auth=auth)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        api_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3.diff"
        }
        
        log(f"[*] Downloading diff from GitHub...")
        diff_res = requests.get(api_url, headers=headers)
        
        if diff_res.status_code != 200:
            log(f"[!] GitHub API Error: {diff_res.status_code}")
            pr.create_issue_comment(f"❌ Ошибка при обращении к GitHub API, код ошибки: {diff_res.status_code}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        diff_text = diff_res.text

        if not diff_text.strip() or len(diff_text) < 10:
            log("[!] Diff is empty or too short.")
            review_comment = "⚠️ Не удалось найти изменения в коде или они слишком малы для анализа."
        else:
            review_comment = get_ai_review(diff_text)

        final_message = f"{CONFIG['ai_review']['footer_message']}{review_comment}"
        pr.create_issue_comment(final_message)
        
        log(f"[x] Success. Review published.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        log(f"[!] Critical worker error: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main() -> None:
    log(f"[*] Worker started. Model: {CONFIG['ai_review']['model']}")
    
    while True:
        try:
            parameters = pika.URLParameters(RABBIT_URL)
            connection = pika.BlockingConnection(parameters)

            channel = connection.channel()
            channel.queue_declare(queue='tasks', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='tasks', on_message_callback=process)
            
            log("--- ✔ Connection established. Waiting for tasks... ---")
            channel.start_consuming()
            
        except pika.exceptions.AMQPConnectionError:
            log("--- ❌ RabbitMQ unavailable. Retrying in 5s... ---")
            time.sleep(5)
            continue
        except Exception as e:
            log(f"--- ⚠️ Unexpected error: {e} ---")
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("[⚠️] Worker stopped by user.")
        sys.exit(0)