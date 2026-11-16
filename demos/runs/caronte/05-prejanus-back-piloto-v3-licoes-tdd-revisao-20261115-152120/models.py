from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    nusp: Mapped[str | None] = mapped_column(String)
    research_field: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Edict(Base):
    __tablename__ = "edict"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    candidate_forms: Mapped[str | None] = mapped_column(String)
    recommenders_forms: Mapped[str | None] = mapped_column(String)
    closed_date: Mapped[date] = mapped_column(Date)
    year: Mapped[int] = mapped_column(Integer)
    semester: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String)
    phase: Mapped[str] = mapped_column(String)
    is_open: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accept_forms: Mapped[str | None] = mapped_column(String)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="SET NULL")
    )


class EdictPhase(Base):
    __tablename__ = "edict_phase"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edict_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("edict.id", ondelete="CASCADE")
    )
    closed_date: Mapped[date | None] = mapped_column(Date)
    phase: Mapped[str] = mapped_column(String)


class EdictFormMapping(Base):
    __tablename__ = "edict_form_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edict_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("edict.id", ondelete="CASCADE")
    )
    form_type: Mapped[str] = mapped_column(
        Enum("candidate", "recommender", name="form_type_enum")
    )
    mapping: Mapped[dict] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    form_id: Mapped[str | None] = mapped_column(String)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE")
    )
    form_version: Mapped[int] = mapped_column(Integer)


class Submission(Base):
    __tablename__ = "submission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edict_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("edict.id", ondelete="CASCADE")
    )
    advisor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    candidate_form_id: Mapped[int] = mapped_column(Integer)
    recommender_form_ids: Mapped[list | None] = mapped_column(JSON)
    stats: Mapped[str] = mapped_column(String, default="underreview")
    accept_form_id: Mapped[int | None] = mapped_column(Integer)
    entry_semester: Mapped[str | None] = mapped_column(String)
    letter_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    recommender_form_version: Mapped[int] = mapped_column(Integer, default=1)
    candidate_form_version: Mapped[int] = mapped_column(Integer, default=1)


class Comment(Base):
    __tablename__ = "comment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE")
    )
    submission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("submission.id", ondelete="CASCADE")
    )
    comment: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    submission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("submission.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE")
    )
    submission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("submission.id", ondelete="CASCADE")
    )
    label: Mapped[str] = mapped_column(String)
    color: Mapped[str] = mapped_column(String)
    context_type: Mapped[str | None] = mapped_column(String)


class PrivateNote(Base):
    __tablename__ = "private_note"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE")
    )
    submission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("submission.id", ondelete="CASCADE")
    )
    note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SubmissionView(Base):
    __tablename__ = "submission_view"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE")
    )
    submission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("submission.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserEdictSlot(Base):
    __tablename__ = "user_edict_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE")
    )
    edict_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("edict.id", ondelete="CASCADE")
    )
    slots: Mapped[int | None] = mapped_column(Integer)
