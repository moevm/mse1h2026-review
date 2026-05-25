import os
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.main import app
from app.api.routes import get_service, get_config_service
from app.core.database import get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_dependencies():
    mock_review_service = MagicMock()
    mock_config_service = MagicMock()
    mock_db_session = MagicMock()
    
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_service] = lambda: mock_review_service
    app.dependency_overrides[get_config_service] = lambda: mock_config_service

    yield mock_review_service, mock_config_service
    app.dependency_overrides.clear()

@pytest.mark.parametrize(
    "action,body,has_pr,expected_status,expected_json_status",
    [
        ("created", "/ai-review check code", True, 200, "dispatched"),
        ("opened", "/ai-review check code", True, 200, "dispatched"),
        ("created", "/ai-feedback like", True, 200, "feedback changed"),
        ("edited", "/ai-review check code", True, 200, "ignored"),
        ("created", "just regular comment", True, 200, "ignored"),
        ("created", "/ai-review check code", False, 200, "ignored"),
    ],
)
def test_handle_external_webhook_scenarios(
    action, body, has_pr, expected_status, expected_json_status
):
    payload = {
        "action": action,
        "comment": {"body": body},
        "issue": {"number": 123},
        "repository": {"name": "test-repo", "owner": {"login": "test-owner"}},
    }
    if has_pr:
        payload["issue"]["pull_request"] = {"url": "http://api.github.com"}

    response = client.post("/worker/webhook", json=payload)
    assert response.status_code == expected_status
    assert response.json()["status"] == expected_json_status

def test_create_review_valid_data(mock_dependencies):
    mock_review_service, _ = mock_dependencies
    
    mock_review_response = MagicMock()
    mock_review_response.id = 1
    mock_review_response.comment_count = 5
    mock_review_response.duration_ms = 1200
    mock_review_service.save_review.return_value = mock_review_response

    valid_payload = {
        "comment_count": 5,
        "duration_ms": 1200,
        "statistics": {"style": 2, "bug": 1}
    }
    response = client.post(
        "/worker/repos/owner/repo/pulls/1/reviews", json=valid_payload
    )
    assert response.status_code == 200

def test_create_review_invalid_data():
    invalid_payload = {"wrong_field": "garbage"}
    response = client.post(
        "/worker/repos/owner/repo/pulls/1/reviews", json=invalid_payload
    )
    assert response.status_code == 422

def test_get_global_metrics_defaults(mock_dependencies):
    mock_review_service, _ = mock_dependencies
    mock_review_service.get_filtered_stats.return_value = {
        "total_reviews": 0,
        "total_comments": 0,
        "avg_duration_ms": 0.0,
        "chart_data": {},
    }

    response = client.get("/admin/stats")
    assert response.status_code == 200
    assert response.json() == {
        "total_reviews": 0,
        "total_comments": 0,
        "avg_duration_ms": 0.0,
        "chart_data": {},
    }
    mock_review_service.get_filtered_stats.assert_called_once_with(
        repo_id=None, days=7
    )

def test_get_pr_analytics_success(mock_dependencies):
    mock_review_service, _ = mock_dependencies
    mock_review_service.get_pr_details.return_value = {
        "pr_number": 1,
        "latest_review_date": "2026-05-24T12:00:00",
        "chart_data": {},
        "comment_count": 0,
        "duration_ms": 0,
        "is_liked": None
    }

    response = client.get("/admin/repos/owner/repo/pulls/1")
    assert response.status_code == 200
    assert response.json()["pr_number"] == 1

def test_get_pr_analytics_not_found(mock_dependencies):
    mock_review_service, _ = mock_dependencies
    mock_review_service.get_pr_details.return_value = None

    response = client.get("/admin/repos/owner/repo/pulls/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Статистика не найдена"

def test_get_all_prs_filled(mock_dependencies):
    mock_review_service, _ = mock_dependencies
    mock_review_service.get_all_pull_requests_summary.return_value = [
        {"owner": "owner", "repo": "repo", "pr_number": 1, "last_update": None, "reviews_count": 1}
    ]

    response = client.get("/admin/pulls")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1

def test_get_all_prs_empty(mock_dependencies):
    mock_review_service, _ = mock_dependencies
    mock_review_service.get_all_pull_requests_summary.return_value = []

    response = client.get("/admin/pulls")
    assert response.status_code == 200
    assert response.json() == []

def test_http_method_not_allowed():
    response = client.post("/admin/pulls", json={})
    assert response.status_code == 405

def test_response_has_json_content_type():
    response = client.get("/admin/pulls")
    assert "application/json" in response.headers["content-type"].lower()

def test_cors_headers_present():
    headers = {"Origin": "http://localhost:3000"}
    response = client.get("/admin/pulls", headers=headers)
    assert "access-control-allow-credentials" in response.headers or "access-control-allow-origin" in response.headers
