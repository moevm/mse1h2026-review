from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.domain import Repository, PullRequest, Review, ReviewStatItem
from app.core.config import RABBIT_HOST, RABBIT_PASS, RABBIT_USER
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException
import json
import pika


class ReviewService:
    def __init__(self, db: Session):
        self.db = db


    def send_to_broker(self, message: dict):
        try:
            credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
            parameters = pika.ConnectionParameters(
                host=RABBIT_HOST, 
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue='webhook_queue', durable=True)
            
            channel.basic_publish(
                exchange='',
                routing_key='webhook_queue',
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            connection.close()
        except Exception as e:
            print(f"!!! ОШИБКА RABBITMQ: {type(e).__name__}: {e}")
            raise HTTPException(status_code=500, detail=f"Broker error: {str(e)}") from e


    def save_review(self, owner: str, repo_name: str, pr_num: int, data):
        repo = self.db.query(Repository).filter_by(owner=owner, name=repo_name).first()
        if not repo:
            repo = Repository(owner=owner, name=repo_name)
            self.db.add(repo); 
            self.db.flush()

        pr = self.db.query(PullRequest).filter_by(repo_id=repo.id, number=pr_num).first()
        if not pr:
            pr = PullRequest(repo_id=repo.id, number=pr_num)
            self.db.add(pr); 
            self.db.flush()

        new_review = Review(
            pr_id=pr.id, 
            comment_count=data.comment_count, 
            duration_ms=data.duration_ms
        )
        self.db.add(new_review); 
        self.db.flush()

        for cat, count in data.statistics.items():
            self.db.add(ReviewStatItem(review_id=new_review.id, category=cat, issue_count=count))
        
        self.db.commit()
        return new_review

    def get_pr_details(self, owner: str, name: str, pr_num: int):
        review = self.db.query(Review).join(PullRequest).join(Repository)\
            .filter(Repository.owner == owner, Repository.name == name, PullRequest.number == pr_num)\
            .order_by(Review.created_at.desc()).first()
        
        if not review: 
            return None
        
        return {
            "pr_number": pr_num,
            "latest_review_date": review.created_at,
            "chart_data": {s.category: s.issue_count for s in review.stats},
            "comment_count": review.comment_count,
            "duration_ms": review.duration_ms,
            "is_liked": review.is_liked
        }

    def get_global_stats(self):
        stats = self.db.query(
            func.count(Review.id),
            func.sum(Review.comment_count),
            func.avg(Review.duration_ms)
        ).first()
        return {
            "total_reviews": stats[0] or 0,
            "total_comments": stats[1] or 0,
            "avg_duration_ms": float(stats[2] or 0)
        }
    



    def get_filtered_stats(self, repo_id: Optional[int] = None, days: int = 7):
        start_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(
            func.count(Review.id),
            func.sum(Review.comment_count),
            func.avg(Review.duration_ms)
        ).filter(Review.created_at >= start_date)
        
        if repo_id:
            query = query.join(PullRequest).filter(PullRequest.repo_id == repo_id)
            
        stats = query.first()
        

        error_query = self.db.query(
            ReviewStatItem.category, 
            func.sum(ReviewStatItem.issue_count)
        ).join(Review).filter(Review.created_at >= start_date)
        
        if repo_id:
            error_query = error_query.join(PullRequest).filter(PullRequest.repo_id == repo_id)
            
        error_stats = error_query.group_by(ReviewStatItem.category).all()
        
        return {
            "total_reviews": stats[0] or 0,
            "total_comments": stats[1] or 0,
            "avg_duration_ms": float(stats[2] or 0),
            "chart_data": {cat: count for cat, count in error_stats}
        }
    

    def get_all_pull_requests_summary(self):
        query = self.db.query(
            Repository.owner,
            Repository.name.label("repo_name"),
            PullRequest.number,
            func.max(Review.created_at).label("last_update"),
            func.count(Review.id).label("total_reviews")
        ).join(PullRequest, Repository.id == PullRequest.repo_id) \
        .outerjoin(Review, PullRequest.id == Review.pr_id) \
        .group_by(Repository.owner, Repository.name, PullRequest.number) \
        .all()

        return [
            {
                "owner": r.owner,
                "repo": r.repo_name,
                "pr_number": r.number,
                "last_update": r.last_update,
                "reviews_count": r.total_reviews
            } for r in query
        ]
    