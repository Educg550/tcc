from __future__ import annotations

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
Base = declarative_base()

class Form(Base):
    __tablename__ = "form"
    id = Column(Integer, primary_key=True)

class FormShared(Base):
    __tablename__ = "form_shared"
    id = Column(Integer, primary_key=True)
    form_id = Column(Integer)
    token = Column(String)

class FormResponse(Base):
    __tablename__ = "form_response"
    id = Column(Integer, primary_key=True)
    form_id = Column(Integer)
    shared_id = Column(Integer)

class Responses(Base):
    __tablename__ = "responses"
    id = Column(Integer, primary_key=True)
    response_id = Column(Integer)