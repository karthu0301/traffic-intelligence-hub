import io
import os
import uuid
import zipfile
from unittest.mock import patch, MagicMock
from datetime import timedelta
from pathlib import Path

from sqlmodel import Session, select
from fastapi.testclient import TestClient

from main.backend.db import engine
from main.backend.auth.utils import create_access_token
from main.backend.models import User, DetectionRecord

# point at the literal "runs/results" directory, to match the existing download endpoint
results_dir = Path("runs") / "results"


def test_static_file_serving():
    unique_name = "test_static_file_serving_unique.jpg"
    static_path = results_dir / unique_name
    static_path.parent.mkdir(parents=True, exist_ok=True)
    static_path.write_bytes(b"fake image content")

    client = TestClient(__import__("main.backend.main", fromlist=["app"]).app)
    res = client.get(f"/static/results/{unique_name}")
    assert res.status_code == 200
    assert res.content == b"fake image content"


def create_user(session: Session) -> User:
    user = User(email="test@example.com", hashed_password="hashed")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def upload_image(client: TestClient, filename="test.jpg", headers=None):
    fake_image = io.BytesIO(b"fake image data")
    files = [("files", (filename, fake_image, "image/jpeg"))]
    return client.post("/upload", files=files, headers=headers or {})


def test_upload(client, override_get_session):
    resp = upload_image(client)
    assert resp.status_code == 200
    data = resp.json()[0]
    assert data["filename"] == "test.jpg"
    assert "annotated_image" in data
    assert data["saved"] is False


def test_history(client, override_get_session):
    with Session(engine) as sess:
        create_user(sess)

    token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(hours=1),
    )
    headers = {"Authorization": f"Bearer {token}"}

    upload_image(client, headers=headers)
    res = client.get("/history", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_search(client, override_get_session):
    with Session(engine) as sess:
        create_user(sess)

    token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(hours=1),
    )
    headers = {"Authorization": f"Bearer {token}"}

    upload_image(client, "searchme.jpg", headers=headers)
    res = client.get("/search", params={"filename_query": "searchme"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] >= 1


def test_result(client, override_get_session):
    with Session(engine) as sess:
        create_user(sess)

    token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(hours=1),
    )
    headers = {"Authorization": f"Bearer {token}"}

    upload_image(client, "detailed.jpg", headers=headers)
    with Session(engine) as sess:
        record = sess.exec(
            select(DetectionRecord).where(DetectionRecord.filename == "detailed.jpg")
        ).first()

    res = client.get(f"/result/{record.id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["filename"] == "detailed.jpg"


def test_download(client, override_get_session):
    # 1. create user
    with Session(engine) as sess:
        create_user(sess)

    # 2. get auth headers
    token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(hours=1),
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 3. upload under a unique name
    unique_filename = f"test_download_{uuid.uuid4().hex}.jpg"
    upload_image(client, unique_filename, headers=headers)

    # 4. ensure record exists
    with Session(engine) as sess:
        record = sess.exec(
            select(DetectionRecord).where(DetectionRecord.filename == unique_filename)
        ).first()
    assert record is not None, "DetectionRecord not found!"

    # 5. write the dummy file into runs/results
    file_path = results_dir / unique_filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(b"fake image content")

    # 6. download it
    res = client.get(f"/download/{unique_filename}", headers=headers)
    assert res.status_code == 200
    assert res.content == b"fake image content"


def test_download_all(client, override_get_session):
    with Session(engine) as sess:
        create_user(sess)

    token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(hours=1),
    )
    headers = {"Authorization": f"Bearer {token}"}

    upload_image(client, "multi1.jpg", headers=headers)
    upload_image(client, "multi2.jpg", headers=headers)

    with Session(engine) as sess:
        records = sess.exec(select(DetectionRecord)).all()
        for r in records:
            # write each annotated and crop into runs/results
            ann = Path(r.annotated_image).name
            crop = Path(r.annotated_image).name  # assume same folder
            (results_dir / ann).parent.mkdir(parents=True, exist_ok=True)
            (results_dir / ann).write_bytes(b"fake image content")
            (results_dir / crop).write_bytes(b"fake image content")

    res = client.get("/download-all", headers=headers)
    assert res.status_code == 200
    zp = io.BytesIO(res.content)
    with zipfile.ZipFile(zp) as z:
        assert any(name.endswith(".jpg") for name in z.namelist())


@patch("main.backend.routes.detection.run_llm_task")
def test_ask(mock_llm_task, client, override_get_session):
    with Session(engine) as sess:
        create_user(sess)

    mock_res = MagicMock()
    mock_res.id = "mock_task_123"
    mock_llm_task.apply_async.return_value = mock_res

    token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(hours=1),
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/ask",
        json={"question": "What are the most frequent plates?"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["task_id"] == "mock_task_123"
