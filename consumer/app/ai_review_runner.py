import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime

import requests
import structlog

logger = structlog.get_logger()
config_src_path = "/app/config/.ai-review.json"


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

            for line in pull_resp.iter_lines():
                if line:
                    chunk = json.loads(line.decode())
                    status = chunk.get("status")
                    log.info("pull_progress", status=status)

            log.info("model_pulled_successfully")
        else:
            log.debug("model_exists")

    except Exception as e:
        log.error("ollama_api_error", error=str(e))
        raise RuntimeError(f"Ollama API error while pulling model: {e}")


def run_ai_review_for_pr(repo_url: str, repo_name: str, repo_owner: str, pr_number: str, branch: str):
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
        config_dst_path = os.path.join(temp_dir, ".ai-review.json")
        if not os.path.exists(config_src_path):
            raise FileNotFoundError(f"Config not found at {config_src_path}")
        shutil.copy(config_src_path, config_dst_path)

        with open(config_dst_path, "r") as f:
            config = json.load(f)
            model_name = config["llm"]["meta"]["model"]
            ensure_ollama_model(model_name)

        config["vcs"]["pipeline"]["owner"] = repo_owner
        config["vcs"]["pipeline"]["repo"] = repo_name
        config["vcs"]["pipeline"]["pull_number"] = str(pr_number)
        config["vcs"]["http_client"]["api_token"] = os.getenv("GITHUB_TOKEN", "")

        with open(config_dst_path, "w") as f:
            json.dump(config, f, indent=2)

        log.info("running_ai_review_tool")

        subprocess.run(["ai-review", "clear-inline"], cwd=temp_dir, check=True)
        subprocess.run(["ai-review", "show-config"], cwd=temp_dir, check=True)
        subprocess.run(["ai-review", "run-inline"], cwd=temp_dir, check=True)

        log.info("ai_review_finished")

        # TODO: сохранить результат в БД (время, статус, артефакты)

    except Exception as e:
        log.error("ai_review_failed", error=str(e))

    finally:
        shutil.rmtree(temp_dir)
        log.debug("cleanup_finished", temp_dir=temp_dir)
