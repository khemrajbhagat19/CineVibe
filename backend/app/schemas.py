from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    is_admin: bool
    is_active: bool


class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    genre: str
    release_year: int
    duration_seconds: int
    views: int
    thumbnail_url: str | None = None
    stream_url: str | None = None
    created_at: datetime


class MovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    genre: str = Field(min_length=1, max_length=80)
    release_year: int = Field(ge=1888, le=2100)


class ProgressUpdate(BaseModel):
    progress: float = Field(ge=0, le=100)


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
