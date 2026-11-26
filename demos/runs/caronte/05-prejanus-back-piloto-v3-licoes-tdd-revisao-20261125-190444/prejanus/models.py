from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum as SAEnum, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    nusp: Mapped[str | None] = mapped_column(String, nullable=True)
    research_field: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Edict(Base):
    __tablename__ = "edict"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    candidate_forms: Mapped[str | None] = mapped_column(String, nullable=True)
    recommenders_forms: Mapped[str | None] = mapped_column(String, nullable=True)
    closed_date: Mapped[date] = mapped_column(Date)
    year: Mapped[int] = mapped_column(Integer)
    semester: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String)
    phase: Mapped[str] = mapped_column(String)
    is_open: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accept_forms: Mapped[str | None] = mapped_column(String, nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class EdictPhase(Base):
    __tablename__ = "edict_phase"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edict_id: Mapped[int] = mapped_column(Integer)
    closed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    phase: Mapped[str] = mapped_column(String)


class EdictFormMapping(Base):
    __tablename__ = "edict_form_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edict_id: Mapped[int] = mapped_column(Integer)
    form_type: Mapped[str] = mapped_column(SAEnum("candidate", "recommender", name="form_type_enum"))
    mapping: Mapped[dict] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    form_id: Mapped[str | None] = mapped_column(String, nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    form_version: Mapped[int] = mapped_column(Integer)


class Submission(Base):
    __tablename__ = "submission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edict_id: Mapped[int] = mapped_column(Integer)
    advisor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    candidate_form_id: Mapped[int] = mapped_column(Integer)
    recommenders_form_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    stats: Mapped[str] = mapped_column(String, default="underreview")
    accept_form_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    entry_semester: Mapped[str | None] = mapped_column(String, nullable=True)
    letter_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    recommender_form_version: Mapped[int] = mapped_column(Integer)
    candidate_form_version: Mapped[int] = mapped_column(Integer)


class Comment(Base):
    __tablename__ = "comment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    submission_id: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    submission_id: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String)
    color: Mapped[str] = mapped_column(String)
    context_type: Mapped[str | None] = mapped_column(String, nullable=True)


class PrivateNote(Base):
    __tablename__ = "private_note"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    submission_id: Mapped[int] = mapped_column(Integer)
    note: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SubmissionView(Base):
    __tablename__ = "submission_view"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    submission_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UserEdictSlots(Base):
    __tablename__ = "user_edict_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    edict_id: Mapped[int] = mapped_column(Integer)
    slots: Mapped[int | None] = mapped_column(Integer, nullable=True)
