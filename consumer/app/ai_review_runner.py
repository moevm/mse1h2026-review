import yaml
import json
import os
import shutil
import subprocess
import tempfile
import time

import requests
import structlog

from process_artifacts import process_folder
from get_settings import (
    fetch_repo_config,
    fetch_repo_prompt,
    apply_config_update,
    write_prompt_md,
)

BACKEND_URL = "http://backend:8000"
BASE_CONFIG_PATH = "/app/config/.ai-review.yaml"

logger = structlog.get_logger()


def ensure_ollama_model(model: str):
    base_url = "http://ollama:11434"
    log = logger.bind(model=model)

    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=30)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]

        if model not in models:
            log.info("pulling_ollama_model")

            pull_resp = requests.post(f"{base_url}/api/pull", json={"name": model}, stream=True, timeout=600)
            pull_resp.raise_for_status()

            last_status = None
            last_print = time.time()

            for line in pull_resp.iter_lines():
                if not line:
                    continue
                try:
                    msg = line.decode()
                    last_status = msg
                    chunk = json.loads(msg)
                    status = chunk.get("status")
                    log.info("pull_progress", status=status)
                except Exception:
                    continue

                if time.time() - last_print >= 5:
                    if last_status:
                        log.info("pull_progress_status", status=last_status)
                    last_print = time.time()

            log.info("model_pulled_successfully")

    except Exception as e:
        log.error("ollama_api_error", error=str(e))
        raise RuntimeError(f"Ollama API error while pulling model: {e}")


def send_review_to_backend(owner, repo, pr_number, stats, duration_ms):
    payload = {
        "comment_count": stats["comment_count"],
        "duration_ms": duration_ms,
        "statistics": {**stats["error_type_stats"], **stats["error_topic_stats"]},
    }

    url = f"{BACKEND_URL}/worker/repos/{owner}/{repo}/pulls/{pr_number}/reviews"

    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()

    logger.info("review_sent_to_backend", owner=owner, repo=repo, pr_number=pr_number)
    return resp.json()


def run_ai_review_for_pr(
    repo_url: str,
    repo_name: str,
    repo_owner: str,
    pr_number: str,
    branch: str,
):
    log = logger.bind(repo=f"{repo_owner}/{repo_name}", pr=pr_number, branch=branch)
    temp_dir = tempfile.mkdtemp(prefix=f"ai-review-{repo_name}")

    try:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")

        if repo_url.startswith("https://"):
            auth_repo_url = repo_url.replace("https://", f"https://{github_token}@")
        else:
            auth_repo_url = repo_url

        log.info("cloning_repository", temp_dir=temp_dir)

        subprocess.run(
            ["git", "clone", "--branch", branch, auth_repo_url, temp_dir], check=True, capture_output=True, text=True
        )

        config_path = os.path.join(temp_dir, ".ai-review.yaml")
        shutil.copy(BASE_CONFIG_PATH, config_path)

        log.info("fetching_repo_settings")

        config_data = fetch_repo_config(repo_owner, repo_name)
        prompt_data = fetch_repo_prompt(repo_owner, repo_name)

        apply_config_update(
            yaml_path=config_path,
            model_config=config_data,
            prompt_config=prompt_data,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pr_number=pr_number,
            api_token=github_token
        )

        prompt_path = os.path.join(temp_dir, "prompt.md")
        write_prompt_md(prompt_data, prompt_path)

        model_name = config_data["model"]
        ensure_ollama_model(model_name)

        log.info("running_ai_review")

        start_time = time.time()
        subprocess.run(["ai-review", "clear-inline"], cwd=temp_dir, check=True)
        subprocess.run(["ai-review", "show-config"], cwd=temp_dir, check=True)
        subprocess.run(["ai-review", "run-inline"], cwd=temp_dir, check=True)

        duration_ms = int((time.time() - start_time) * 1000)
        log.info("ai_review_finished")
        log.info("ai_review_duration_ms", duration_ms=duration_ms)

        artifacts_path = os.path.join(temp_dir, "artifacts", "llm")
        stats = process_folder(artifacts_path)
        log.info("artifacts_processed")
        send_review_to_backend(
            owner=repo_owner, repo=repo_name, pr_number=pr_number, stats=stats, duration_ms=duration_ms
        )

    except Exception as e:
        log.error("ai_review_failed", error=str(e))

    finally:
        shutil.rmtree(temp_dir)
        log.debug("cleanup_finished", temp_dir=temp_dir)
