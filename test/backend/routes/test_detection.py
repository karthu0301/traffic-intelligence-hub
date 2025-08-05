import io

async def test_upload_and_history(client):
    fake_image = io.BytesIO(b"fake image data")
    res = await client.post("/upload", files={"files": ("test.jpg", fake_image, "image/jpeg")})
    assert res.status_code == 200
    data = res.json()
    assert data[0]["filename"] == "test.jpg"

    # Verify that history reflects the upload
    res2 = await client.get("/history")
    assert res2.status_code == 200
    assert len(res2.json()) >= 1
