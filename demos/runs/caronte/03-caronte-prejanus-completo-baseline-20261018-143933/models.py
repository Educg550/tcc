"""Modelos do banco PreJanus (esquema reconstruído do original)."""
import uuid
from datetime import datetime

from sqlalchemy import (JSON, Boolean, Date, DateTime, ForeignKey, Integer,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def uid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(255), default="")
    email: Mapped[str] = mapped_column(String(255), unique=True)
    nusp: Mapped[str] = mapped_column(String(64), default="")
    role: Mapped[str] = mapped_column(String(32), default="teacher")


class Edict(Base):
    __tablename__ = "edicts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    year: Mapped[str] = mapped_column(String(16), default="")
    semester: Mapped[str] = mapped_column(String(64), default="")
    edict_type: Mapped[str] = mapped_column(String(64), default="")
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    candidate_form_id: Mapped[str] = mapped_column(String(64), default="")
    recommender_form_id: Mapped[str] = mapped_column(String(64), default="")
    accept_form_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    date_application: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    date_verification: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    date_evaluation: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    date_closed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_phase_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Phase(Base):
    __tablename__ = "phases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    edict_id: Mapped[str] = mapped_column(ForeignKey("edicts.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(32))
    date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Mapping(Base):
    __tablename__ = "mappings"
    __table_args__ = (UniqueConstraint("edict_id", "type", "version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    edict_id: Mapped[str] = mapped_column(ForeignKey("edicts.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(32))  # candidates | recommenders
    version: Mapped[str] = mapped_column(String(32))
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    tree: Mapped[dict] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    edict_id: Mapped[str] = mapped_column(ForeignKey("edicts.id", ondelete="CASCADE"))
    answer_id: Mapped[str] = mapped_column(String(64))
    form_version: Mapped[str] = mapped_column(String(32), default="1")
    accept_form_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stats: Mapped[str] = mapped_column(String(32), default="underreview")
    entry_semester: Mapped[str] = mapped_column(String(64), default="")
    letter_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    advisors: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("edict_id", "answer_id"),)


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (UniqueConstraint("edict_id", "user_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    edict_id: Mapped[str] = mapped_column(ForeignKey("edicts.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[str] = mapped_column(String(16), default="0")


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Favorite(Base):
    __tablename__ = "favorites"
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)


class Label(Base):
    __tablename__ = "labels"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    label: Mapped[str] = mapped_column(String(255))
    color: Mapped[str] = mapped_column(String(32), default="")
    context: Mapped[str] = mapped_column(String(32), default="candidate")


class PrivateNote(Base):
    __tablename__ = "private_notes"
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    note: Mapped[str] = mapped_column(Text, default="")


class View(Base):
    __tablename__ = "views"
    __table_args__ = (UniqueConstraint("user_id", "submission_id", "date"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    date: Mapped[object] = mapped_column(Date)


class Bidding(Base):
    __tablename__ = "biddings"
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    bidding: Mapped[str] = mapped_column(String(64), default="")


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    edict_id: Mapped[str] = mapped_column(String(36))
    kind: Mapped[str] = mapped_column(String(16))  # pdf | csv
    status: Mapped[str] = mapped_column(String(32), default="processing")
    filename: Mapped[str] = mapped_column(String(255), default="")
