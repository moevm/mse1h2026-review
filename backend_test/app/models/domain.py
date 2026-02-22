from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)

    pulls = relationship("PullRequest", back_populates="repo")


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"))
    pr_number = Column(Integer, index=True, nullable=False)

    repo = relationship("Repository", back_populates="pulls")
    reviews = relationship("ReviewStat", back_populates="pull", uselist=False)


class ReviewStat(Base):
    __tablename__ = "review_stats"

    id = Column(Integer, primary_key=True, index=True)
    pr_id = Column(Integer, ForeignKey("pull_requests.id"), unique=True)
    statistics = Column(JSONB, nullable=False)                      # {"syntax_error": 2, "logic_error": 1} etc
    is_liked = Column(Boolean, nullable=True)                       # True, False или None

    pull = relationship("PullRequest", back_populates="reviews")