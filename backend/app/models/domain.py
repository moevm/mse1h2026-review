from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Repository(Base):
    __tablename__ = "repositories"
    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)
    pulls = relationship("PullRequest", back_populates="repo", cascade="all, delete-orphan")

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