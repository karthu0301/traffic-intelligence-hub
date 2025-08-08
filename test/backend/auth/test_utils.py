import pytest
from datetime import datetime, timedelta
from main.backend.models import User
from sqlmodel import Session
from main.backend.db import get_session
from main.backend.auth.utils import create_access_token

def test_me_authenticated(client, override_get_session, test_engine):
    with Session(test_engine) as session:
        session.add(User(email="authuser@example.com", hashed_password="hashed"))
        session.commit()

    token = create_access_token(
        data={"sub": "authuser@example.com"},
        expires_delta=timedelta(hours=1)
    )
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"email": "authuser@example.com"}

def test_me_anonymous(client):
    response = client.get("/me")
    assert response.status_code == 200
    assert response.json() == {"user": None}

def test_me_invalid_token(client):
    response = client.get("/me", headers={"Authorization": "Bearer invalid.token"})
    assert response.status_code == 401
