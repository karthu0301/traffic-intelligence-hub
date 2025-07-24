from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from passlib.hash import bcrypt

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str

    uploads: List["DetectionRecord"] = Relationship(back_populates="user")

class DetectionRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    filename: str
    timestamp: str
    annotated_image: str
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="uploads")


class PlateInfo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    detection_id: int = Field(foreign_key="detectionrecord.id")
    plate_crop_path: str
    plate_string: str
    plate_confidence: float


class CharacterBox(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    detection_id: int = Field(foreign_key="detectionrecord.id")
    class_id: int
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int
