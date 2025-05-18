import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from app.main import app

@pytest.fixture
def mock_redis():
    with patch("redis.asyncio.Redis") as mock:
        redis_mock = AsyncMock()
        mock.return_value = redis_mock
        yield redis_mock

@pytest.mark.asyncio
async def test_create_task(mock_redis):
    mock_redis.set.return_value = True
    with patch("asyncio.create_task"):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/api/tasks",
                json={
                    "name": "test_task",
                    "parameters": {"param1": "value1"},
                    "callback_url": "http://example.com/callback",
                },
            )
    assert response.status_code == 200
    assert "task_id" in response.json()

@pytest.mark.asyncio
async def test_create_task_missing_parameters(mock_redis):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/tasks",
            json={
                "name": "test_task",
                "callback_url": "http://example.com/callback"
            },
        )
    assert response.status_code == 422
    assert any("parameters" in err["loc"] for err in response.json()["detail"])

@pytest.mark.asyncio
async def test_create_task_invalid_callback_url(mock_redis):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/tasks",
            json={
                "name": "test_task",
                "parameters": {"param1": "value1"},
                "callback_url": "not-a-valid-url"
            },
        )
    assert response.status_code == 422
    assert any("callback_url" in str(err["loc"]) for err in response.json()["detail"])

@pytest.mark.asyncio
async def test_create_task_empty_name(mock_redis):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/tasks",
            json={
                "name": "",
                "parameters": {"param1": "value1"},
                "callback_url": "http://example.com/callback"
            },
        )
    assert response.status_code == 422
    assert any("name" in str(err["loc"]) for err in response.json()["detail"])