from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel
from pathlib import Path
from db import engine
from auth.routes import router as auth_router
from routes.detection import router as detection_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.50.143:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
RUNS_DIR = BASE_DIR / "runs"

app.mount("/static", StaticFiles(directory=str(RUNS_DIR)), name="static")

app.include_router(auth_router)
app.include_router(detection_router)

SQLModel.metadata.create_all(engine)
