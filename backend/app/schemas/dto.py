from pydantic import BaseModel
from typing import Dict, Optional, List


# для воркера
class ReviewCreate(BaseModel):
    statistics: Dict[str, int]


class ReviewUpdateLike(BaseModel):
    is_liked: bool


# для админ-панели
class RepositoryResponse(BaseModel):
    owner: str
    name: str

    class Config:
        orm_mode = True


class RepoStatsResponse(BaseModel):
    total_prs_reviewed: int
    aggregated_errors: Dict[str, int]
    total_likes: int
    total_dislikes: int