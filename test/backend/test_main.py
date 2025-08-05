async def test_root_endpoints_exist(client):
    # Check at least one known endpoint
    res = await client.get("/history")
    assert res.status_code == 200
