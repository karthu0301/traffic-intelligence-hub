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
from main.backend.main import RUNS_DIR
from main.backend.models import User, DetectionRecord
from main.backend.auth.utils import create_access_token

results_dir = RUNS_DIR / "results"

def test_static_file_serving():
    # Use a UNIQUE name here
    unique_name = "test_static_file_serving_unique.jpg"
    static_path = results_dir / unique_name
    static_path.parent.mkdir(parents=True, exist_ok=True)
    with open(static_path, "wb") as f:
        f.write(b"fake image content")

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
            select(DetectionRecord)
            .where(DetectionRecord.filename == "detailed.jpg")
        ).first()

    res = client.get(f"/result/{record.id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["filename"] == "detailed.jpg"

def test_download(client, override_get_session):
    import uuid
    from pathlib import Path

    with Session(engine) as sess:
        create_user(sess)

    token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(hours=1),
    )
    headers = {"Authorization": f"Bearer {token}"}

    unique_filename = f"test_download_{uuid.uuid4().hex}.jpg"
    upload_image(client, unique_filename, headers=headers)

    with Session(engine) as sess:
        record = sess.exec(
            select(DetectionRecord).where(DetectionRecord.filename == unique_filename)
        ).first()

    assert record is not None, "DetectionRecord not found for uploaded unique file!"

    # Always create the file in the actual download location
    file_path = results_dir / unique_filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(b"fake image content")

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
        results_dir.mkdir(parents=True, exist_ok=True)
        for r in records:
            fname = r.annotated_image.split("/")[-1]
            file_path = results_dir / fname
            file_path.write_bytes(b"fake image content")
            r.annotated_image = str(file_path)  # PATCH!
            sess.add(r)
        sess.commit()

    res = client.get("/download-all", headers=headers)
    assert res.status_code == 200
    zp = io.BytesIO(res.content)
    with zipfile.ZipFile(zp) as z:
        assert any(name.endswith(".jpg") for name in z.namelist())

    # Second round: test again (optional, for coverage)
    upload_image(client, "multi1.jpg", headers=headers)
    upload_image(client, "multi2.jpg", headers=headers)
    with Session(engine) as sess:
        records = sess.exec(select(DetectionRecord)).all()
        results_dir.mkdir(parents=True, exist_ok=True)
        for r in records:
            fname = r.annotated_image.split("/")[-1]
            (results_dir / fname).write_bytes(b"fake image content")

    res = client.get("/download-all", headers=headers)
    assert res.status_code == 200
    zp = io.BytesIO(res.content)
    with zipfile.ZipFile(zp) as z:
        assert any(name.endswith(".jpg") for name in z.namelist())

def test_delete(client, override_get_session):
    with Session(engine) as sess:
        create_user(sess)

    token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(hours=1),
    )
    headers = {"Authorization": f"Bearer {token}"}

    upload_image(client, "delete_me.jpg", headers=headers)
    with Session(engine) as sess:
        record = sess.exec(select(DetectionRecord)).first()

    res = client.delete(f"/delete/{record.id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["message"] == "Record deleted"

def test_plate_frequency(client, override_get_session):
    with Session(engine) as sess:
        create_user(sess)

    token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(hours=1),
    )
    headers = {"Authorization": f"Bearer {token}"}

    upload_image(client, "freq.jpg", headers=headers)
    res = client.get("/plate-frequency", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 1

def test_accuracy_trends(client, override_get_session):
    with Session(engine) as sess:
        create_user(sess)

    token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(hours=1),
    )
    headers = {"Authorization": f"Bearer {token}"}

    upload_image(client, "trend.jpg", headers=headers)
    res = client.get("/detection-accuracy-trends", headers=headers)
    assert res.status_code == 200
    trends = res.json()
    assert isinstance(trends, list)
    assert "avg_confidence" in trends[0]

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
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["task_id"] == "mock_task_123"
