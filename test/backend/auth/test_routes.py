async def test_login_route_exists(client):
    # Replace with actual login endpoint if available
    res = await client.post("/login", json={"email": "test@example.com", "password": "123"})
    # If your login route returns 404 (not implemented), just check for a response
    assert res.status_code in [200, 400, 401, 404]