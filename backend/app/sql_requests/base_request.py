from sqlalchemy import func, desc
from app.models.domain import Review, ReviewStatItem, PullRequest

def get_latest_project_state(db: Session, repo_id: int):
    subquery = db.query(
        Review.pr_id,
        func.max(Review.created_at).label("max_date")
    ).join(PullRequest).filter(PullRequest.repo_id == repo_id).group_by(Review.pr_id).subquery()

    stats = db.query(
        PullRequest.number,
        ReviewStatItem.category,
        func.sum(ReviewStatItem.issue_count)
    ).join(Review, PullRequest.id == Review.pr_id)\
     .join(subquery, (Review.pr_id == subquery.c.pr_id) & (Review.created_at == subquery.c.max_date))\
     .join(ReviewStatItem, Review.id == ReviewStatItem.review_id)\
     .group_by(PullRequest.number, ReviewStatItem.category)\
     .all()

    return stats