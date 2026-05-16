from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Repository(Base):
    __tablename__ = "repositories"
    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)
    pulls = relationship("PullRequest", back_populates="repo", cascade="all, delete-orphan")
    model_config = relationship("ModelConfig", back_populates="repo", cascade="all, delete-orphan")
    prompt_config = relationship("PromptConfig", back_populates="repo", cascade="all, delete-orphan")

class PullRequest(Base):
    __tablename__ = "pull_requests"
    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"))
    number = Column(Integer, nullable=False)
    repo = relationship("Repository", back_populates="pulls")
    reviews = relationship("Review", back_populates="pr", cascade="all, delete-orphan")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    pr_id = Column(Integer, ForeignKey("pull_requests.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Метрики из ТЗ
    comment_count = Column(Integer, default=0)
    duration_ms = Column(Integer, nullable=True) 
    is_liked = Column(Boolean, nullable=True)
    
    pr = relationship("PullRequest", back_populates="reviews")
    stats = relationship("ReviewStatItem", back_populates="review", cascade="all, delete-orphan")

class ReviewStatItem(Base):
    __tablename__ = "review_stat_items"
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"))
    category = Column(String, nullable=False)
    issue_count = Column(Integer, default=0)
    review = relationship("Review", back_populates="stats")

class SystemLog(Base):
    __tablename__ = "system_logs"
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String)
    module = Column(String)
    message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ModelConfig(Base):
    __tablename__ = "model_config"
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True, unique=True)
    model = Column(String)
    max_tokens = Column(Integer) 
    temperature = Column(Float)
    num_ctx = Column(Integer)
    top_p = Column(Float)
    repeat_penalty = Column(Float)
    seed = Column(Integer)
    llm_http_client_timeout = Column(Float)
    vcs_http_client_timeout = Column(Float)
    concurrency = Column(Integer)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    repo = relationship("Repository", back_populates="model_config")


class PromptConfig(Base):
    __tablename__ = "prompt_config"
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True, unique=True)
    prompt_text = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    mode = Column(String)
    repo = relationship("Repository", back_populates="prompt_config")


