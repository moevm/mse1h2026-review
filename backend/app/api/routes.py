from typing import Optional

import structlog
from app.core.database import get_db
from app.schemas.dto import GlobalStatsResponse, PRDetailsResponse, ReviewCreate
from app.services.review_service import ReviewService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

worker_router = APIRouter()
admin_router = APIRouter()


def get_service(db: Session = Depends(get_db)):
    return ReviewService(db)


@worker_router.post("/webhook")
async def handle_external_webhook(data: dict, s: ReviewService = Depends(get_service)):
    comment = data.get("comment", {})
    body = comment.get("body", "").strip()

    if body != "/ai-review":
        return {"status": "ignored", "message": "No /ai-review command found"}

    if not data.get("issue", {}).get("pull_request"):
        return {"status": "ignored", "message": "Not a pull request"}

    s.send_to_broker(data)
    return {"status": "dispatched", "message": "Data is in the queue"}


@admin_router.get("/stats", response_model=GlobalStatsResponse)
def get_global_metrics(days: int = 7, repo_id: Optional[int] = None, s: ReviewService = Depends(get_service)):
    return s.get_filtered_stats(repo_id=repo_id, days=days)


@worker_router.post("/repos/{owner}/{repo}/pulls/{pr_num}/reviews")
def create_review(owner: str, repo: str, pr_num: int, data: ReviewCreate, s: ReviewService = Depends(get_service)):
    return s.save_review(owner, repo, pr_num, data)


@admin_router.get("/repos/{owner}/{repo}/pulls/{pr_num}", response_model=PRDetailsResponse)
def get_pr_analytics(owner: str, repo: str, pr_num: int, s: ReviewService = Depends(get_service)):
    res = s.get_pr_details(owner, repo, pr_num)
    if not res:
        raise HTTPException(status_code=404, detail="Статистика не найдена")
    return res


@admin_router.get("/pulls")
def get_all_prs(s: ReviewService = Depends(get_service)):
    return s.get_all_pull_requests_summary()
