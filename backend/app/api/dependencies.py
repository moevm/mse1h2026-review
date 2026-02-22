from app.core.database import SessionLocal
from app.services.review_service import ReviewService
from fastapi import Depends


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_review_service(db=Depends(get_db)) -> ReviewService:
    return ReviewService(db)