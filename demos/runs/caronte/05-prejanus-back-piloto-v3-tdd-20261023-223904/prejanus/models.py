import datetime
import json as _json

from sqlalchemy import JSON, Boolean, Date, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PassthroughJSON(JSON):
    """psycopg3 já converte json/jsonb; evita re-parse do valor já desserializado."""

    def result_processor(self, dialect, coltype):
        def process(value):
            if isinstance(value, (str, bytes)):
                return _json.loads(value)
            return value

        return process


class PassthroughJSONB(JSONB):
    def result_processor(self, dialect, coltype):
        def process(value):
            if isinstance(value, (str, bytes)):
                return _json.loads(value)
            return value

        return process


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    nusp: Mapped[str | None] = mapped_column(String)
    research_field: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))


class Edict(Base):
    __tablename__ = "edict"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    candidate_forms: Mapped[str | None] = mapped_column(String)
    recommenders_forms: Mapped[str | None] = mapped_column(String)
    closed_date: Mapped[datetime.date] = mapped_column(Date)
    year: Mapped[int] = mapped_column(Integer)
    semester: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String)
    phase: Mapped[str] = mapped_column(String)
    is_open: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    accept_forms: Mapped[str | None] = mapped_column(String)
    user_id: Mapped[int | None] = mapped_column(Integer)


class EdictPhase(Base):
    __tablename__ = "edict_phase"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edict_id: Mapped[int] = mapped_column(Integer)
    closed_date: Mapped[datetime.date | None] = mapped_column(Date)
    phase: Mapped[str] = mapped_column(String)


class EdictFormMapping(Base):
    __tablename__ = "edict_form_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edict_id: Mapped[int] = mapped_column(Integer)
    form_type: Mapped[str] = mapped_column(String)
    mapping: Mapped[dict] = mapped_column(PassthroughJSONB)
    is_active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    form_id: Mapped[str | None] = mapped_column(String)
    user_id: Mapped[int | None] = mapped_column(Integer)
    form_version: Mapped[int] = mapped_column(Integer)


class Submission(Base):
    __tablename__ = "submission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edict_id: Mapped[int] = mapped_column(Integer)
    advisor_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    candidate_form_id: Mapped[int] = mapped_column(Integer)
    recommender_form_ids: Mapped[list | None] = mapped_column(
        "recommenders_form_ids", PassthroughJSON
    )
    stats: Mapped[str] = mapped_column(String, default="underreview")
    accept_form_id: Mapped[int | None] = mapped_column(Integer)
    entry_semester: Mapped[str | None] = mapped_column(String)
    letter_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    recommender_form_version: Mapped[int] = mapped_column(Integer)
    candidate_form_version: Mapped[int] = mapped_column(Integer)


class Comment(Base):
    __tablename__ = "comment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    submission_id: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))


class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    submission_id: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String)
    color: Mapped[str] = mapped_column(String)
    context_type: Mapped[str | None] = mapped_column(String)


class PrivateNote(Base):
    __tablename__ = "private_note"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    submission_id: Mapped[int] = mapped_column(Integer)
    note: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))


class SubmissionView(Base):
    __tablename__ = "submission_view"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    submission_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))


class UserEdictSlots(Base):
    __tablename__ = "user_edict_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    edict_id: Mapped[int] = mapped_column(Integer)
    slots: Mapped[int | None] = mapped_column(Integer)
