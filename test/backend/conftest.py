# test/backend/conftest.py
import os
import pytest

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine, Session

import main.backend.auth.utils as auth_utils
import main.backend.auth.routes as auth_routes
from main.backend.db import get_session
from main.backend.main import app

# 1) Shared in-memory DB
TEST_DB_URL = "sqlite:///:memory:"
_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@pytest.fixture(scope="session", autouse=True)
def patch_engine():
    import main.backend.db
    main.backend.db.engine = _engine


# 2) Create & drop tables once per test session
@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    SQLModel.metadata.create_all(_engine)
    yield
    SQLModel.metadata.drop_all(_engine)

# 3) Expose the engine for tests that need it
@pytest.fixture(scope="session")
def test_engine():
    return _engine

# 4) Override FastAPI dependency to use our in-memory DB
@pytest.fixture
def override_get_session(test_engine):
    def _get_session_override():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override
    yield
    app.dependency_overrides.clear()

# 5) Monkey-patch JWT and SendGrid so auth endpoints don’t blow up
@pytest.fixture(autouse=True)
def patch_jwt_and_sendgrid(monkeypatch):
    # ensure create_access_token & verify_token use a real key
    monkeypatch.setenv("SECRET_KEY", "testsecretkey")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setattr(auth_utils,  "SECRET_KEY", "testsecretkey", raising=False)
    monkeypatch.setattr(auth_utils,  "ALGORITHM",  "HS256",            raising=False)
    monkeypatch.setattr(auth_routes, "SECRET_KEY", "testsecretkey", raising=False)
    monkeypatch.setattr(auth_routes, "ALGORITHM",  "HS256",            raising=False)

    # stub out SendGrid
    monkeypatch.setenv("SENDGRID_API_KEY",     "dummy")
    monkeypatch.setenv("SENDGRID_SENDER_EMAIL","noreply@test")
    class FakeResponse:
        status_code = 202
        body = b""
    class FakeSGClient:
        def __init__(self, api_key=None): pass
        def send(self, message): return FakeResponse()
    monkeypatch.setattr(
        auth_routes.sendgrid,
        "SendGridAPIClient",
        FakeSGClient,
        raising=True
    )

# 6) Provide a TestClient that's wired to your FastAPI app
@pytest.fixture
def client(override_get_session):
    return TestClient(app)

# 7) Fake out YOLO detection everywhere it’s imported
@pytest.fixture(autouse=True)
def mock_yolo(monkeypatch):
    def fake_detect(path):
        return {
            # what your save logic expects:
            "annotated_image":        "/static/results/fake.jpg",
            "annotated_image_path":   "/static/results/fake.jpg",
            "detections": [
                {
                    "plate_string":        "FAKE123",
                    "plate_confidence":    0.95,
                    "plate_crop_path":     "/static/results/crop.jpg",
                    "annotated_crop_path": "/static/results/crop.jpg",
                    "characters":          []
                }
            ]
        }

    # patch the service function
    monkeypatch.setattr(
        "main.backend.services.yolo.detect_plates_and_characters",
        fake_detect
    )
    # patch the already-imported name in the route module
    monkeypatch.setattr(
        "main.backend.routes.detection.detect_plates_and_characters",
        fake_detect
    )
