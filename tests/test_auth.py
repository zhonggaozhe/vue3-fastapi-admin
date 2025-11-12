import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    response = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin", "device_id": "test-device"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["role"] == "admin"
    assert payload["user"]["permissions"] == ["*:*:*"] or "*.*.*" in payload["user"]["permissions"]
    assert payload["session"]["sid"].startswith("sess_")


@pytest.mark.asyncio
async def test_login_invalid_password(client):
    response = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_user_list_endpoint(client):
    response = await client.get("/users/")
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 2
    assert next(user for user in users if user["username"] == "admin")["roles"][0]["code"] == "admin"
