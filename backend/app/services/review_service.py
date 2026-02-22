from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.domain import Repository, PullRequest, ReviewStat
from app.schemas.dto import ReviewCreate


class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def _get_or_create_repo(self, owner: str, repo_name: str) -> Repository:
        repo = self.db.query(Repository).filter_by(owner=owner,
                                                   name=repo_name).first()
        if not repo:
            repo = Repository(owner=owner, name=repo_name)
            self.db.add(repo)
            self.db.commit()
            self.db.refresh(repo)
        return repo

    def _get_or_create_pr(self, repo_id: int, pr_number: int) -> PullRequest:
        pr = self.db.query(PullRequest).filter_by(repo_id=repo_id,
                                                  pr_number=pr_number).first()
        if not pr:
            pr = PullRequest(repo_id=repo_id, pr_number=pr_number)
            self.db.add(pr)
            self.db.commit()
            self.db.refresh(pr)
        return pr

    def save_or_update_review(self, owner: str, repo_name: str, pr_number: int,
                              data: ReviewCreate):
        repo = self._get_or_create_repo(owner, repo_name)
        pr = self._get_or_create_pr(repo.id, pr_number)

        review = self.db.query(ReviewStat).filter_by(pr_id=pr.id).first()

        if review:
            review.statistics = data.statistics
        else:
            review = ReviewStat(pr_id=pr.id, statistics=data.statistics)
            self.db.add(review)

        self.db.commit()
        return {"status": "success", "message": "Review stats saved"}

    def update_like_status(self, owner: str, repo_name: str,
                           pr_number: int, is_liked: bool):
        repo = self.db.query(Repository).filter_by(owner=owner,
                                                   name=repo_name).first()
        if not repo:
            return {"status": "error", "message": "Repository not found"}

        pr = self.db.query(PullRequest).filter_by(repo_id=repo.id,
                                                  pr_number=pr_number).first()
        if not pr:
            return {"status": "error", "message": "PR not found"}

        review = self.db.query(ReviewStat).filter_by(pr_id=pr.id).first()
        if review:
            review.is_liked = is_liked
            self.db.commit()
            return {"status": "success", "message": "Like status updated"}
        return {"status": "error", "message": "Review not found"}

    def get_repositories(self):
        return self.db.query(Repository).all()

    def get_aggregated_stats(self, owner: str, repo_name: str):
        # Заглушка для агрегации. Тут пока что упрощенно

        repo = self.db.query(Repository).filter_by(owner=owner,
                                                   name=repo_name).first()
        if not repo:
            return None

        prs = self.db.query(PullRequest).filter_by(repo_id=repo.id).all()
        pr_ids = [pr.id for pr in prs]

        reviews = self.db.query(ReviewStat).filter(ReviewStat.pr_id.in_(pr_ids)).all()

        agg_errors = {}
        likes = dislikes = 0

        for r in reviews:
            for err_type, count in r.statistics.items():
                agg_errors[err_type] = agg_errors.get(err_type, 0) + count
            if r.is_liked is True:
                likes += 1
            elif r.is_liked is False:
                dislikes += 1

        return {
            "total_prs_reviewed": len(reviews),
            "aggregated_errors": agg_errors,
            "total_likes": likes,
            "total_dislikes": dislikes
        }
