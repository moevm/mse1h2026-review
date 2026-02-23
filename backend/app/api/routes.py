from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas.dto import ReviewCreate, ReviewUpdateLike, RepositoryResponse, RepoStatsResponse
from app.services.review_service import ReviewService

router = APIRouter()
worker_router = APIRouter(prefix="/worker", tags=["Worker"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])

def get_service():
    return ReviewService()


@worker_router.post("/repos/{owner}/{repo}/pulls/{pr_number}/reviews")
def ingest_review_stats(owner: str, repo: str, pr_number: int, data: ReviewCreate, service: ReviewService = Depends(get_service)):
    return service.save_or_update_review(owner, repo, pr_number, data)


@worker_router.patch("/repos/{owner}/{repo}/pulls/{pr_number}/reviews/like")
def update_review_feedback(owner: str, repo: str, pr_number: int, data: ReviewUpdateLike, service: ReviewService = Depends(get_service)):
    return service.update_like_status(owner, repo, pr_number, data.is_liked)


@admin_router.get("/repos", response_model=List[RepositoryResponse])
def list_repos(service: ReviewService = Depends(get_service)):
    return service.get_repositories()


@admin_router.get("/repos/{owner}/{repo}/stats", response_model=RepoStatsResponse)
def get_stats(owner: str, repo: str, service: ReviewService = Depends(get_service)):
    stats = service.get_aggregated_stats(owner, repo)
    if not stats:
        raise HTTPException(status_code=404, detail="Repo stats not found")
    return stats