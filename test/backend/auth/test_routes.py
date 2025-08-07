import pytest
from httpx import AsyncClient, ASGITransport
from main.backend.main import app
from main.backend.auth.utils import create_access_token
from datetime import timedelta

TEST_EMAIL = "test@example.com"

@pytest.mark.asyncio
async def test_send_magic_link_creates_user(override_get_session): 
    async with AsyncClient(
         transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        res = await ac.post("/send-magic-link", json={"email": TEST_EMAIL})
    
    assert res.status_code == 200
    assert res.json() == {"msg": "Magic link sent"}

@pytest.mark.asyncio
async def test_verify_token():
    token = create_access_token(
        data={"sub": TEST_EMAIL},
        expires_delta=timedelta(minutes=15)
    )

    async with AsyncClient(
         transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        res = await ac.post("/verify-token", json={"token": token})

    assert res.status_code == 200
    assert res.json()["email"] == TEST_EMAIL
