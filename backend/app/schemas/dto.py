from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, Optional
from datetime import datetime

class ReviewCreate(BaseModel):
    statistics: Dict[str, int]
    comment_count: int
    duration_ms: int

class PRDetailsResponse(BaseModel):
    pr_number: int
    latest_review_date: datetime
    chart_data: Dict[str, int]
    comment_count: int
    duration_ms: int
    is_liked: Optional[bool]
    
    model_config = ConfigDict(from_attributes=True)

class GlobalStatsResponse(BaseModel):
    total_reviews: int
    total_comments: int
    avg_duration_ms: float
    chart_data: Dict[str, int]

class ModelConfigResponse(BaseModel):
    model: str
    max_tokens: int 
    temperature: float
    num_ctx: int
    top_p: float
    repeat_penalty: float
    seed: int
    llm_http_client_timeout: float
    vcs_http_client_timeout: float
    concurrency: int
    updated_at: datetime

class PromptConfigResponse(BaseModel):
    mode: str
    prompt_text: str
    updated_at: datetime


class ModelConfigUpdate(BaseModel):
    model: str = Field(..., description="Название модели, например, llama3")
    max_tokens: int = Field(..., ge=1)
    temperature: float = Field(..., ge=0.0, le=2.0)
    num_ctx: int = Field(..., ge=1)
    top_p: float = Field(..., ge=0.0, le=1.0)
    repeat_penalty: float = Field(..., ge=0.0)
    seed: int
    llm_http_client_timeout: float = Field(..., ge=0.0)
    vcs_http_client_timeout: float = Field(..., ge=0.0)
    concurrency: int = Field(..., ge=1)

    class Config:
        from_attributes = True


class PromptConfigUpdate(BaseModel):
    prompt_text: str = Field(..., description="Тело системного промта для ИИ")
    mode: str

    class Config:
        from_attributes = True    


class RepositoryShortResponse(BaseModel):
    id: int
    owner: str
    name: str

    class Config:
        from_attributes = True        