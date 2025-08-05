from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import Session, select
from db import engine
from models import User
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    # no Authorization header → anonymous
    if not token:
        return None

    # otherwise validate
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            return None
        with Session(engine) as session:
            return session.exec(select(User).where(User.email == email)).first()
    except JWTError:
        # header was present but token invalid → reject
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
