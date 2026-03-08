from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Optional
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