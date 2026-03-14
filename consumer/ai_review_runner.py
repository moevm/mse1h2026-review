import os
import json
import subprocess
import tempfile
import shutil
from datetime import datetime


def run_ai_review_for_pr(repo_url: str, repo_name:str, repo_owner:str, pr_number: str, branch: str):

    temp_dir = tempfile.mkdtemp(prefix="ai-review-")
    try:
        print(f"[{datetime.now()}] Cloning repo {repo_url} (branch {branch}) into {temp_dir}", flush=True)
        subprocess.run(
            ["git", "clone", "--branch", branch, repo_url, temp_dir],
            check=True
        )

        config = {
            "llm": {
                "provider": "OLLAMA",
                "meta": {
                    "model": "minimax-m2.5:cloud",
                    "max_tokens": 2000,
                    "temperature": 0.3,
                    "num_ctx": 2048,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                    "stop": ["USER:", "SYSTEM:"],
                    "seed": 42
                },
                "http_client": {
                    "api_url": "http://localhost:11434"
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
            "review": {
                "mode": "FULL_FILE_DIFF",
                "dry_run": False,
                "inline_tag": "#ai-review-inline",
                "summary_tag": "#ai-review-summary"
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