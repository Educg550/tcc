"""ORM models for the PreJanus database."""
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    nusp: Mapped[str | None] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(32), default="teacher")
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class Edict(Base):
    __tablename__ = "edicts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int] = mapped_column(Integer)
    semester: Mapped[int] = mapped_column(Integer)
    edict_type: Mapped[str] = mapped_column(String(64))
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    candidate_form_id: Mapped[str] = mapped_column(String(64))
    recommender_form_id: Mapped[str] = mapped_column(String(64))
    accept_form_id: Mapped[str | None] = mapped_column(String(64))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    phase: Mapped[str] = mapped_column(String(32), default="inscricoes")
    closed_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    phases: Mapped[list["EdictPhase"]] = relationship(
        back_populates="edict",
        cascade="all, delete-orphan",
        order_by="EdictPhase.id",
    )


class EdictPhase(Base):
    __tablename__ = "edict_phases"

    id: Mapped[int] = mapped_column(primary_key=True)
    edict_id: Mapped[int] = mapped_column(ForeignKey("edicts.id", ondelete="CASCADE"))
    phase: Mapped[str] = mapped_column(String(32))
    closed_date: Mapped[date | None] = mapped_column(Date)

    edict: Mapped[Edict] = relationship(back_populates="phases")


class FormMapping(Base):
    __tablename__ = "form_mappings"
    __table_args__ = (
        UniqueConstraint("edict_id", "form_type", "version", name="uq_mapping"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    edict_id: Mapped[int] = mapped_column(ForeignKey("edicts.id", ondelete="CASCADE"))
    form_type: Mapped[str] = mapped_column(String(32))  # candidates | recommenders
    version: Mapped[int] = mapped_column(Integer)
    tree: Mapped[dict] = mapped_column(JSON)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    edict_id: Mapped[int] = mapped_column(ForeignKey("edicts.id", ondelete="CASCADE"))
    token: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    phone_number: Mapped[str] = mapped_column(String(64), default="")
    nationality: Mapped[str] = mapped_column(String(128), default="")
    personal_website: Mapped[str] = mapped_column(String(255), default="")
    gender: Mapped[str] = mapped_column(String(32), default="")
    birth_date: Mapped[date | None] = mapped_column(Date)
    lattes_curriculum: Mapped[str] = mapped_column(String(255), default="")
    stats: Mapped[str] = mapped_column(String(32), default="underreview")
    version: Mapped[int] = mapped_column(Integer, default=1)
    accept_form_id: Mapped[int | None] = mapped_column(Integer)
    letter_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    entry_semester: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)

    edict: Mapped[Edict] = relationship()


class SubmissionAdvisor(Base):
    __tablename__ = "submission_advisors"
    __table_args__ = (UniqueConstraint("submission_id", name="uq_advisor"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (UniqueConstraint("edict_id", "user_id", name="uq_slot"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    edict_id: Mapped[int] = mapped_column(ForeignKey("edicts.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    amount: Mapped[str] = mapped_column(String(16), default="0")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE")
    )
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "submission_id", name="uq_favorite"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE")
    )
    label: Mapped[str] = mapped_column(String(128))
    color: Mapped[str] = mapped_column(String(32))
    context: Mapped[str] = mapped_column(String(32), default="candidate")
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class PrivateNote(Base):
    __tablename__ = "private_notes"
    __table_args__ = (
        UniqueConstraint("user_id", "submission_id", name="uq_private_note"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE")
    )
    note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class SubmissionView(Base):
    __tablename__ = "submission_views"
    __table_args__ = (
        UniqueConstraint("user_id", "submission_id", "view_date", name="uq_view"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE")
    )
    view_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class Bidding(Base):
    __tablename__ = "biddings"
    __table_args__ = (
        UniqueConstraint("user_id", "submission_id", name="uq_bidding"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE")
    )
    bidding: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)