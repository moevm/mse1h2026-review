import requests
import yaml
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

def get_repo_id(owner: str, repo: str) -> int:
    """Получает ID репозитория от бекенда"""
    url = f"{BACKEND_URL}/worker/repo/id"
    resp = requests.get(url, params={"owner": owner, "repo": repo}, timeout=30)
    resp.raise_for_status()
    return resp.json()["id"]

def fetch_repo_config(owner: str, repo: str) -> dict:
    """Получает json от бекенда с конфигом для данного репозитория"""
    repo_id = get_repo_id(owner, repo)
    url = f"{BACKEND_URL}/worker/config/model"
    resp = requests.get(url, params={"repo_id": repo_id}, timeout=30)
    resp.raise_for_status()
    return resp.json()

def fetch_repo_prompt(owner: str, repo: str) -> dict:
    """Получает json от бекенда с промптом для данного репозитория"""
    repo_id = get_repo_id(owner, repo)
    url = f"{BACKEND_URL}/worker/config/prompt"
    resp = requests.get(url, params={"repo_id": repo_id}, timeout=30)
    resp.raise_for_status()
    return resp.json()

def apply_config_update(
    yaml_path: str,
    model_config: dict | None = None,
    prompt_config: dict | None = None,
    repo_owner: str | None = None,
    repo_name: str | None = None,
    pr_number: str | None = None,
    api_token: str | None = None,
):
    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    if model_config:
        llm = config.setdefault("llm", {}).setdefault("meta", {})

        llm["model"] = model_config.get("model", llm.get("model"))
        llm["max_tokens"] = model_config.get("max_tokens", llm.get("max_tokens"))
        llm["temperature"] = model_config.get("temperature", llm.get("temperature"))
        llm["num_ctx"] = model_config.get("num_ctx", llm.get("num_ctx"))
        llm["top_p"] = model_config.get("top_p", llm.get("top_p"))
        llm["repeat_penalty"] = model_config.get("repeat_penalty", llm.get("repeat_penalty"))
        llm["seed"] = model_config.get("seed", llm.get("seed"))

        config.setdefault("llm", {}).setdefault("http_client", {})[
            "timeout"
        ] = model_config.get(
            "llm_http_client_timeout",
            config.get("llm", {}).get("http_client", {}).get("timeout"),
        )

        config.setdefault("core", {})["concurrency"] = model_config.get(
            "concurrency",
            config.get("core", {}).get("concurrency"),
        )

    if prompt_config:
        config.setdefault("review", {})["mode"] = prompt_config.get(
            "mode",
            config.get("review", {}).get("mode"),
        )

    if repo_owner or repo_name or pr_number:
        vcs_section = config.setdefault("vcs", {})

        vcs_section.setdefault("http_client", {})["api_token"] = api_token
        
        pipeline = vcs_section.setdefault("pipeline", {})
        if repo_owner:
            pipeline["owner"] = repo_owner
        if repo_name:
            pipeline["repo"] = repo_name
        if pr_number:
            pipeline["pull_number"] = str(pr_number)

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False, allow_unicode=True)


def write_prompt_md(prompt_data: dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(prompt_data.get("prompt_text", ""))
