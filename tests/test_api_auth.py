async def test_register_success(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "api_key" in data
    assert len(data["api_key"]) > 0
    assert data["credits"] == 10
    assert "message" in data


async def test_register_returns_unique_api_keys(client):
    r1 = await client.post("/api/v1/auth/register", json={"email": "a@example.com"})
    r2 = await client.post("/api/v1/auth/register", json={"email": "b@example.com"})
    assert r1.json()["api_key"] != r2.json()["api_key"]


async def test_register_duplicate_email_returns_409(client):
    await client.post("/api/v1/auth/register", json={"email": "duplicate@example.com"})
    response = await client.post(
        "/api/v1/auth/register", json={"email": "duplicate@example.com"}
    )
    assert response.status_code == 409


async def test_register_invalid_email_returns_422(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email"},
    )
    assert response.status_code == 422


async def test_register_missing_email_returns_422(client):
    response = await client.post("/api/v1/auth/register", json={})
    assert response.status_code == 422
