from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ormparams.mixin import ORMParamsMixin

DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
Base = declarative_base()


class User(Base, ORMParamsMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    age = Column(Integer, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    posts = relationship("Post", back_populates="author")

    ORMPARAMS_FIELDS = "*"
    ORMPARAMS_OPERATIONS = "*"


class UserCreate(BaseModel):
    age: int
    username: str


class UserResponse(BaseModel):
    id: int
    age: int
    username: str
    created_at: datetime


class Post(Base, ORMParamsMixin):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    author = relationship("User", back_populates="posts")

    ORMPARAMS_FIELDS = "*"
    ORMPARAMS_OPERATIONS = "*"


class PostCreate(BaseModel):
    title: str
    author_id: int


class PostResponse(BaseModel):
    id: int
    title: str
    author_id: int
    created_at: datetime
