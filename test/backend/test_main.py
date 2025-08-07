import os
import shutil
import uuid
import pytest
from fastapi.testclient import TestClient
from main.backend.main import app, RUNS_DIR

client = TestClient(app)

@pytest.fixture(scope="module")
def unique_static_file():
    # Use a unique name for every test module run!
    unique_name = f"testfile_{uuid.uuid4().hex}.jpg"
    static_path = RUNS_DIR / "results" / unique_name
    static_path.parent.mkdir(parents=True, exist_ok=True)
    with open(static_path, "wb") as f:
        f.write(b"fake image content")
    yield unique_name
    try:
        static_path.unlink()
    except FileNotFoundError:
        pass
    # Optional: Remove runs dir if you want
    # shutil.rmtree(RUNS_DIR / "results", ignore_errors=True)

def test_static_file_serving(unique_static_file):
    url = f"/static/results/{unique_static_file}"
    res = client.get(url)
    assert res.status_code == 200
    assert res.content == b"fake image content"

def test_cors_headers():
    res = client.options("/upload", headers={
        "Origin": "http://192.168.50.143:3000",
        "Access-Control-Request-Method": "POST"
    })
    assert res.status_code in (200, 204)
    assert res.headers.get("access-control-allow-origin") == "http://192.168.50.143:3000"

@pytest.mark.parametrize("url", [
    "/upload",                     # detection
    "/history",                    # detection
    "/llm/ask",                    # LLM
    "/analytics/plate-frequency",  # analytics
])
def test_routes_respond_to_options(url):
    res = client.options(url)
    assert res.status_code in (200, 204)
