from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from passlib.hash import bcrypt
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str

    uploads: List["DetectionRecord"] = Relationship(back_populates="user")

class DetectionRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    filename: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    annotated_image: str
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="uploads")

    plates: List["PlateInfo"] = Relationship(back_populates="detection")
    characters: List["CharacterBox"] = Relationship(back_populates="detection")

    feedback: Optional[str] = None  
    model_version: Optional[str] = None 
    confidence_threshold: Optional[float] = None


class PlateInfo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    detection_id: int = Field(foreign_key="detectionrecord.id")
    detection: "DetectionRecord" = Relationship(back_populates="plates")
    plate_crop_path: str
    plate_string: str
    plate_confidence: float


class CharacterBox(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    detection_id: int = Field(foreign_key="detectionrecord.id")
    class_id: int
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int
