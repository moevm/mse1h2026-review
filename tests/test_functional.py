import pytest
import httpx

API_URL = "http://backend:8000"

@pytest.mark.asyncio
async def test_webhook_ai_review_success():
    payload = {
        "action": "created",
        "comment": {"body": "/ai-review please check this"},
        "issue": {"number": 123},
        "repository": {"id": 1, "name": "test-repo", "owner": {"login": "test-owner"}}
    }
    async with httpx.AsyncClient(base_url=API_URL) as ac:
        response = await ac.post("/worker/webhook", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] in ["dispatched", "ignored"]

@pytest.mark.asyncio
async def test_webhook_ignored_command():
    payload = {
        "comment": {"body": "hello world"},
    }
    async with httpx.AsyncClient(base_url=API_URL) as ac:
        response = await ac.post("/worker/webhook", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"

@pytest.mark.asyncio
async def test_webhook_unsupported_action():
    payload = {
        "action": "edited",
        "comment": {"body": "/ai-review"},
        "issue": {"pull_request": {}}
    }
    async with httpx.AsyncClient(base_url=API_URL) as ac:
        response = await ac.post("/worker/webhook", json=payload)
    assert response.json()["status"] == "ignored"
    assert "is not supported" in response.json()["message"]

@pytest.mark.asyncio
async def test_get_stats_defaults():
    async with httpx.AsyncClient(base_url=API_URL) as ac:
        response = await ac.get("/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert "chart_data" in data

@pytest.mark.asyncio
async def test_get_pr_details_404():
    async with httpx.AsyncClient(base_url=API_URL) as ac:
        response = await ac.get("/admin/repos/none/none/pulls/99999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_pulls_list():
    async with httpx.AsyncClient(base_url=API_URL) as ac:
        response = await ac.get("/admin/pulls")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_create_review_validation_error():
    invalid_payload = {"wrong_field": "data"} 
    async with httpx.AsyncClient(base_url=API_URL) as ac:
        response = await ac.post("/worker/repos/owner/repo/pulls/1/reviews", json=invalid_payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_cors_headers_present():
    headers = {"Origin": "http://localhost:3000"}
    async with httpx.AsyncClient(base_url=API_URL) as ac:
        response = await ac.get("/", headers=headers)
    assert any(h.startswith("access-control-allow-") for h in response.headers.keys())

@pytest.mark.asyncio
async def test_not_allowed_method():
    async with httpx.AsyncClient(base_url=API_URL) as ac:
        response = await ac.post("/admin/pulls", json={})
    assert response.status_code == 405

@pytest.mark.asyncio
async def test_response_is_json():
    async with httpx.AsyncClient(base_url=API_URL) as ac:
        response = await ac.get("/admin/pulls")
    assert "application/json" in response.headers["content-type"]
