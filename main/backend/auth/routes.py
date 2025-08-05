from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from auth.utils import SECRET_KEY, ALGORITHM
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from db import get_session
from models import User
from auth.utils import create_access_token
from sqlmodel import select
from datetime import timedelta
import sendgrid
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
import os

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_SENDER_EMAIL = os.getenv("SENDGRID_SENDER_EMAIL")

router = APIRouter()

class EmailSchema(BaseModel):
    email: EmailStr

@router.post("/send-magic-link")
async def send_magic_link(payload: EmailSchema, db: Session = Depends(get_session)):
    user = db.exec(select(User).where(User.email == payload.email)).first()

    if not user:
        user = User(email=payload.email)
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=15)
    )

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    magic_link = f"{FRONTEND_URL}/magic-login?token={token}"

    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

    message = Mail(
        from_email=SENDGRID_SENDER_EMAIL,
        to_emails=payload.email,
        subject="🔐 Your Magic Login Link",
        plain_text_content=f"Hi,\n\nClick this link to log in:\n{magic_link}"
    )

    try:
        response = sg.send(message)
        if response.status_code >= 400:
            raise Exception(f"SendGrid error: {response.body}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"msg": "Magic link sent"}

@router.post("/verify-token")
async def verify_token(request: Request):
    data = await request.json()
    token = data.get("token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token payload")
        return {"email": email}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
