from httpx import ASGITransport, AsyncClient
import pytest

from app.main import app


async def make_client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health():
    async with await make_client() as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_analytics_overview():
    async with await make_client() as client:
        response = await client.get("/api/v1/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_reports"] >= 20
    assert data["high_risk_cases"] > 0


@pytest.mark.asyncio
async def test_complaints_list_and_detail():
    async with await make_client() as client:
        response = await client.get("/api/v1/complaints")
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) >= 20

        detail = await client.get(f"/api/v1/complaints/{items[0]['id']}")
        assert detail.status_code == 200
        assert detail.json()["case_id"].startswith("case-")


@pytest.mark.asyncio
async def test_vendors_list_and_404():
    async with await make_client() as client:
        response = await client.get("/api/v1/vendors")
        assert response.status_code == 200
        assert len(response.json()["items"]) >= 8

        missing = await client.get("/api/v1/vendors/unknown")
        assert missing.status_code == 404


@pytest.mark.asyncio
async def test_scoring_rankings():
    async with await make_client() as client:
        response = await client.get("/api/v1/scoring/rankings")
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["final_priority_score"] >= items[-1]["final_priority_score"]


@pytest.mark.asyncio
async def test_cases_list_and_detail():
    async with await make_client() as client:
        response = await client.get("/api/v1/cases")
        assert response.status_code == 200
        items = response.json()["items"]
        assert items
        assert items[0]["vendor"]
        assert items[0]["score"]
        assert "complaints" in items[0]
        assert "audit_events" in items[0]

        detail = await client.get(f"/api/v1/cases/{items[0]['case_id']}")
        assert detail.status_code == 200
        data = detail.json()
        assert data["case_id"] == items[0]["case_id"]
        assert data["ticket"] is None or data["ticket"]["case_id"] == data["case_id"]


@pytest.mark.asyncio
async def test_copilot_chat():
    async with await make_client() as client:
        response = await client.post(
            "/api/v1/copilot/chat",
            json={"message": "Which cases are highest priority?"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "operator review" in data["answer"].lower()
    assert data["sources"]
