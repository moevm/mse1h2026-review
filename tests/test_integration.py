import pytest
from unittest.mock import MagicMock
from app.services.config_service import ConfigService
from app.services.review_service import ReviewService
from app.models.domain import Repository

def test_config_service_upsert_logic(db_session):
    repo = Repository(owner="test_owner", name="config_repo")
    db_session.add(repo)
    db_session.flush()

    service = ConfigService(db_session)
    
    class MockData:
        model = "qwen2.5-coder:1.5b"
        max_tokens = 2000
        temperature = 0.5
        num_ctx = 2000
        top_p = 0.9
        repeat_penalty = 1.0
        seed = 42
        llm_http_client_timeout = 60.0
        vcs_http_client_timeout = 60.0
        concurrency = 2

    config = service.update_model_config(repo_id=repo.id, data=MockData())
    assert config.id is not None
    assert config.repository_id == repo.id
    assert config.model == "qwen2.5-coder:1.5b"

    MockData.model = "deepseek-coder"
    updated_config = service.update_model_config(repo_id=repo.id, data=MockData())
    assert updated_config.id == config.id
    assert updated_config.model == "deepseek-coder"


def test_review_service_repository_fetching(db_session):
    ReviewService.send_to_broker = MagicMock()
    service = ReviewService(db_session)

    repo = Repository(owner="test_owner", name="test_repo")
    db_session.add(repo)
    db_session.commit()

    repo_id = service.get_repository_id(owner="test_owner", repo_name="test_repo")
    assert repo_id == repo.id
