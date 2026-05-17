from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.review_service import ReviewService
from app.services.config_service import ConfigService
from app.schemas.dto import (
    ReviewCreate, PRDetailsResponse, GlobalStatsResponse, GlobalLikesResponse,
    ModelConfigResponse, ModelConfigUpdate, 
    PromptConfigResponse, PromptConfigUpdate,
    RepositoryShortResponse
)
from typing import Optional, List


worker_router = APIRouter()
admin_router = APIRouter()

def get_service(db: Session = Depends(get_db)):
    return ReviewService(db)

def get_config_service(db: Session = Depends(get_db)):
    return ConfigService(db)

@worker_router.post("/webhook")
async def handle_external_webhook(
    data: dict, 
    s: ReviewService = Depends(get_service)
):
    
    comment_body = data.get("comment", {}).get("body", "").strip()

    if comment_body.split()[0] not in ["/ai-review", "/ai-feedback"]:
        return {"status": "ignored", "message": "No /ai-review, /ai-feedback command found"}

    if comment_body.startswith("/ai-feedback"):
        parts = comment_body.split()
        if len(parts) < 2 or parts[1].lower() not in ["like", "dislike"]:
            return {"status": "error", "reason": "Invalid feedback format. Use /ai-feedback like/dislike"}
        
        liked = parts[1].lower() == "like"

        pr_num = data.get("issue", {}).get("number")
        repo_data = data.get("repository", {})
        owner = repo_data.get("owner", {}).get("login")
        repo_name = repo_data.get("name")

        if not all([pr_num, owner, repo_name]):
            return {"status": "ignored", "reason": "Missing metadata (PR number, owner, or repo)"}
        s.update_review_feedback(owner, repo_name, pr_num, liked)
        return {"status": "feedback changed", "message": "feedback changed succesfully"}
        
    elif comment_body.startswith("/ai-review"):

        action = data.get("action")
        if action not in ["created", "opened"]:  # GitHub использует "created", GitLab "opened"
            return {
                "status": "ignored",
                "message": f"Action '{action}' is not supported. Only 'created' or 'opened' actions trigger reviews",
            }
        if not data.get("issue", {}).get("pull_request"):
            return {"status": "ignored", "message": "Not a pull request"}
        
    s.send_to_broker(data)
    return {"status": "dispatched", "message": "Data is in the queue"}


@admin_router.get("/stats", response_model=GlobalStatsResponse)
def get_global_metrics(
    days: int = 7,
    repo_id: Optional[int] = None,
    s: ReviewService = Depends(get_service)
):
    return s.get_filtered_stats(repo_id=repo_id, days=days)


@admin_router.get("/repos/likes", response_model=GlobalLikesResponse)
def get_actual_likes_stats(
    repo_id: Optional[int] = None,
    s: ReviewService = Depends(get_service),
):
    return s.get_likes_stats(repo_id=repo_id)

@worker_router.post("/repos/{owner}/{repo}/pulls/{pr_num}/reviews")
def create_review(owner: str, repo: str, pr_num: int, data: ReviewCreate, s: ReviewService = Depends(get_service)):
    return s.save_review(owner, repo, pr_num, data)

@worker_router.post("/repos/{owner}/{repo}/pulls/{pr_num}/feedback")
def update_feedback(owner: str, repo: str, pr_num: int, liked: bool, s: ReviewService = Depends(get_service)):
    res = s.update_review_feedback(owner, repo, pr_num, liked)
    if not res:
        raise HTTPException(status_code=404, detail="Ревью для обновления не найдено")
    return {"status": "updated"}

@worker_router.get("/repo/id")
def get_repo_id(
    owner: str,
    repo: str,
    s: ReviewService = Depends(get_service)
):
    """Получить ID репозитория по owner и repo"""
    repo_id = s.get_repository_id(owner, repo)

    if not repo_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Репозиторий {owner}/{repo} не найден"
        )

    return {"id": repo_id}

@worker_router.get("/config/model", response_model=ModelConfigResponse)
def get_model_config_for_worker(
    repo_id: Optional[int] = None, 
    s: ConfigService = Depends(get_config_service)
):
    config = s.get_model_config(repo_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Конфигурация модели не найдена (база не инициализирована дефолтными значениями)"
        )
    return config


@worker_router.get("/config/prompt", response_model=PromptConfigResponse)
def get_prompt_config_for_worker(
    repo_id: Optional[int] = None, 
    s: ConfigService = Depends(get_config_service)
):
    config = s.get_prompt_config(repo_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Конфигурация промта не найдена"
        )
    return config

@admin_router.get("/repos/{owner}/{repo}/pulls/{pr_num}", response_model=PRDetailsResponse)
def get_pr_analytics(owner: str, repo: str, pr_num: int, s: ReviewService = Depends(get_service)):
    res = s.get_pr_details(owner, repo, pr_num)
    if not res:
        raise HTTPException(status_code=404, detail="Статистика не найдена")
    return res

@admin_router.get("/pulls")
def get_all_prs(s: ReviewService = Depends(get_service)):
    return s.get_all_pull_requests_summary()


def fetch_model_config(repo_id: Optional[int], s: ConfigService, type="model"):
    if type == "model":
        config = s.get_model_config(repo_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Конфигурация модели не найдена (база не инициализирована дефолтными значениями)"
            )
        return config
    
    elif type == "prompt":
        config = s.get_prompt_config(repo_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Конфигурация промта не найдена"
            )
        return config
    
    
@worker_router.get("/config/model", response_model=ModelConfigResponse)
def get_model_config_for_worker(
    repo_id: Optional[int] = None, 
    s: ConfigService = Depends(get_config_service)
):
    return fetch_model_config(repo_id, s, "model")


@worker_router.get("/config/prompt", response_model=PromptConfigResponse)
def get_prompt_config_for_worker(
    repo_id: Optional[int] = None, 
    s: ConfigService = Depends(get_config_service)
):
    return fetch_model_config(repo_id, s, "prompt")


@admin_router.get("/config/model", response_model=ModelConfigResponse)
def get_model_config(
    repo_id: Optional[int] = None, 
    s: ConfigService = Depends(get_config_service)
):
    return fetch_model_config(repo_id, s, "model")


@admin_router.post("/config/model", response_model=ModelConfigResponse)
def update_model_config(
    body: ModelConfigUpdate, 
    repo_id: Optional[int] = None, 
    s: ConfigService = Depends(get_config_service)
):
    return s.update_model_config(repo_id=repo_id, data=body)


# ==========================================
# РУЧКИ ДЛЯ PROMPT CONFIG
# ==========================================

@admin_router.get("/config/prompt", response_model=PromptConfigResponse)
def get_prompt_config(
    repo_id: Optional[int] = None, 
    s: ConfigService = Depends(get_config_service)
):
    return fetch_model_config(repo_id, s, "prompt")


@admin_router.post("/config/prompt", response_model=PromptConfigResponse)
def update_prompt_config(
    body: PromptConfigUpdate, 
    repo_id: Optional[int] = None, 
    s: ConfigService = Depends(get_config_service)
):
    return s.update_prompt_config(repo_id=repo_id, data=body)


@admin_router.get("/repositories", response_model=List[RepositoryShortResponse])
def get_admin_repositories(db: Session = Depends(get_db)):
    service = ReviewService(db)
    return service.get_all_repositories()
