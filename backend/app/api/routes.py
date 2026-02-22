from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.api.dependencies import get_review_service, get_db
from app.services.review_service import ReviewService
from app.schemas.dto import (
    ReviewCreate,
    ReviewUpdateLike,
    RepositoryResponse,
    RepoStatsResponse
)

worker_router = APIRouter(prefix="/worker", tags=["Worker"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])

# Роутеры для воркера


@worker_router.post("/repos/{owner}/{repo}/pulls/{pr_number}/reviews")
def get_review_stats(
    owner: str,
    repo: str,
    pr_number: int,
    data: ReviewCreate,
    service: ReviewService = Depends(get_review_service)
):
    return service.save_or_update_review(owner, repo, pr_number, data)


@worker_router.patch("/repos/{owner}/{repo}/pulls/{pr_number}/reviews/like")
def update_review_feedback(
    owner: str,
    repo: str,
    pr_number: int,
    data: ReviewUpdateLike,
    service: ReviewService = Depends(get_review_service)
):
    return service.update_like_status(owner, repo, pr_number, data.is_liked)


# Роутры админа

@admin_router.get("/repos", response_model=List[RepositoryResponse])
def get_monitored_repos(service: ReviewService = Depends(get_review_service)):
    return service.get_repositories()


@admin_router.get("/repos/{owner}/{repo}/stats",
                  response_model=RepoStatsResponse)
def get_repository_statistics(
    owner: str,
    repo: str,
    service: ReviewService = Depends(get_review_service)
):
    stats = service.get_aggregated_stats(owner, repo)
    if not stats:
        raise HTTPException(status_code=404,
                            detail="Repository not found "
                            "or no stats available")
    return stats
