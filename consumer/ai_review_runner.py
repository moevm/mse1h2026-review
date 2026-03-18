import os
import json
import subprocess
import tempfile
import shutil
from datetime import datetime


def run_ai_review_for_pr(repo_url: str, repo_name:str, repo_owner:str, pr_number: str, branch: str):

    temp_dir = tempfile.mkdtemp(prefix=f"ai-review-{repo_name}")
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        if repo_url.startswith("https://"):
            auth_repo_url = repo_url.replace("https://", f"https://{github_token}@")
        else:
            auth_repo_url = repo_url
            
        print(f"[{datetime.now()}] Cloning repo {repo_url} (branch {branch}) into {temp_dir}", flush=True)
        subprocess.run(
            ["git", "clone", "--branch", branch, auth_repo_url, temp_dir],
            check=True,
            capture_output=True,
            text=True
        )

        config = {
            "llm": {
                "provider": "OLLAMA",
                "meta": {
                    "model": "qwen2.5-coder:1.5b",
                    "max_tokens": 5000,
                    "temperature": 0.3,
                    "num_ctx": 5000,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                    "stop": ["USER:", "SYSTEM:"],
                    "seed": 42
                },
                "http_client": {
                    "api_url": "http://ollama:11434"
                }
            },
            "vcs": {
                "provider": "GITHUB",
                "pipeline": {
                    "owner": repo_owner,
                    "repo": repo_name,
                    "pull_number": str(pr_number)
                },
                "http_client": {
                    "verify": True,
                    "timeout": 120,
                    "api_url": "https://api.github.com",
                    "api_token": os.getenv("GITHUB_TOKEN", "")
                },
                "pagination": {
                    "per_page": 100,
                    "max_pages": 5
                }
            },
            "core": {"concurrency": 7},
            "prompt": {
                "context": {},
                "normalize_prompts": True,
                "context_placeholder": "<<{value}>>",
                "include_inline_system_prompts": True,
                "include_context_system_prompts": True,
                "include_summary_system_prompts": True,
                "include_inline_reply_system_prompts": True,
                "include_summary_reply_system_prompts": True,
                "inline_prompt_files": ["/app/prompt.md"]
            },

            "review": {
                "mode": "FULL_FILE_DIFF",
                "dry_run": False,
                "inline_tag": "#ai-review-inline",
                "inline_reply_tag": "#ai-review-inline-reply",
                "summary_tag": "#ai-review-summary",
                "summary_reply_tag": "#ai-review-summary-reply",
                "context_lines": 10,
                "allow_changes": [],
                "ignore_changes": [],
                "review_removed_marker": " # removed",
                "inline_comment_fallback": True
            },

            "artifacts": {
                "llm_dir": "./artifacts/llm",
                "llm_enabled": True
            }
        }

        config_path = os.path.join(temp_dir, ".ai-review.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        print(f"[{datetime.now()}] Running ai-review for PR #{pr_number}", flush=True)
        subprocess.run(["ai-review", "clear-inline"], cwd=temp_dir, check=True)
        subprocess.run(["ai-review", "show-config"], cwd=temp_dir, check=True)
        subprocess.run(["ai-review", "run-inline"], cwd=temp_dir, check=True)
        print(f"[{datetime.now()}] Finished AI review for PR #{pr_number}", flush=True)
        #TODO: запрос в БД для сохранения информации о выполнении ревью (время, результат, артефакты модели)
    except Exception as e:
        print(f"Script failed: {e}")

    finally:
        shutil.rmtree(temp_dir)
        print(f"[{datetime.now()}] Cleaned up temporary directory {temp_dir}", flush=True)

# if __name__ == "__main__":
#     repo_url = "https://github.com/user/ai_review_test"
#     repo_name = "ai_review_test"
#     repo_owner = "user"
#     pr_number = "1"
#     branch = "my_test_branch"
#     if not repo_url or not pr_number:
#         print("Error: REPO_URL and PR_NUMBER environment variables must be set.")

#     run_ai_review_for_pr(repo_url, repo_name, repo_owner, pr_number, branch)
