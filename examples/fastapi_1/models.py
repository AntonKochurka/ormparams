from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()
engine = create_engine("sqlite:///test.db", echo=True)
SessionLocal = sessionmaker(bind=engine)


class Parent(Base):
    __tablename__ = "parents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    children = relationship("Child", back_populates="parent")


class Child(Base):
    __tablename__ = "children"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    value = Column(Integer)
    parent_id = Column(Integer, ForeignKey("parents.id"))
    parent = relationship("Parent", back_populates="children")


class ChildCreateSchema(BaseModel):
    name: str
    value: int
    parent_id: Optional[int] = None


class ChildReadSchema(BaseModel):
    id: int
    name: str
    value: int

    class Config:
        orm_mode = True


class ParentCreateSchema(BaseModel):
    name: str


class ParentReadSchema(BaseModel):
    id: int
    name: str
    children: List[ChildReadSchema] = []

    class Config:
        orm_mode = True


Base.metadata.create_all(bind=engine)
