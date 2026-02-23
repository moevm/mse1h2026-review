# from sqlalchemy.orm import Session
# from sqlalchemy import func


class ReviewService:

    storage = {
        "stark-industries/repo1": {
            "total_prs": 12,
            "errors": {"syntax_error": 45, "logic_error": 10},
            "likes": 8,
            "dislikes": 2
        }
    }

    def save_or_update_review(self, owner: str, repo: str, pr_number: int, data):
        return {"status": "success", "message": "Review stats saved in memory"}

    def update_like_status(self, owner: str, repo: str, pr_number: int, is_liked: bool):
        return {"status": "success", "message": "Feedback received"}

    def get_repositories(self):
        return [{"owner": "stark-industries", "name": "repo1"}]

    def get_aggregated_stats(self, owner: str, repo: str):
        key = f"{owner}/{repo}"
        repo_data = self.storage.get(key)

        if not repo_data:
            return None

        return {
            "total_prs_reviewed": repo_data["total_prs"],
            "aggregated_errors": repo_data["errors"],
            "total_likes": repo_data["likes"],
            "total_dislikes": repo_data["dislikes"]
        }
