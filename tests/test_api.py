# tests/test_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.anyio
async def test_signup_and_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Signup test user
        response = await ac.post("/auth/signup", json={
            "name": "Test Kid",
            "email": "testkid@example.com",
            "password": "securepassword123",
            "age": 8
        })
        assert response.status_code in [201, 400]

        # 2. Login test user
        response = await ac.post("/auth/login", data={
            "username": "testkid@example.com",
            "password": "securepassword123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

@pytest.mark.anyio
async def test_get_daily_quests_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/quests/daily")
        assert response.status_code == 401