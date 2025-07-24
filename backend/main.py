from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel
from db import engine
from auth.routes import router as auth_router
from routes.detection import router as detection_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="runs"), name="static")

app.include_router(auth_router)
app.include_router(detection_router)

SQLModel.metadata.create_all(engine)
