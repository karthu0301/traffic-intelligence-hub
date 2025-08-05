async def test_ask_question(client):
    res = await client.post("/ask", json={"question": "What plates were detected?"})
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
