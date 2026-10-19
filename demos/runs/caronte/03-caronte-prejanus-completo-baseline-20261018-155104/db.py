import uuid

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from settings import settings


class Base(DeclarativeBase):
    pass


def new_id() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    email: Mapped[str] = mapped_column(String(255), unique=True)
    nusp: Mapped[str] = mapped_column(String(64), default="")
    role: Mapped[str] = mapped_column(String(32), default="teacher")


class Edict(Base):
    __tablename__ = "edicts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    year: Mapped[str] = mapped_column(String(16), default="")
    semester: Mapped[str] = mapped_column(String(16), default="")
    edict_type: Mapped[str] = mapped_column(String(32), default="")
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    candidate_form_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    recommender_form_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    accept_form_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_phase_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    author_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    date_application: Mapped[str | None] = mapped_column(DateTime, nullable=True)
    date_verification: Mapped[str | None] = mapped_column(DateTime, nullable=True)
    date_evaluation: Mapped[str | None] = mapped_column(DateTime, nullable=True)
    date_closed: Mapped[str | None] = mapped_column(DateTime, nullable=True)
    confirmation_deadline: Mapped[str | None] = mapped_column(DateTime, nullable=True)
    send_approval_letter: Mapped[bool] = mapped_column(Boolean, default=False)


class Phase(Base):
    __tablename__ = "phases"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    edict_id: Mapped[str] = mapped_column(String(64), ForeignKey("edicts.id"))
    label: Mapped[str] = mapped_column(String(32))
    position: Mapped[int] = mapped_column(Integer, default=0)


class Mapping(Base):
    __tablename__ = "mappings"
    __table_args__ = (UniqueConstraint("edict_id", "type", "version"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    edict_id: Mapped[str] = mapped_column(String(64), ForeignKey("edicts.id"))
    type: Mapped[str] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(Integer)
    author_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    form_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tree: Mapped[dict] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    edict_id: Mapped[str] = mapped_column(String(64), ForeignKey("edicts.id"))
    response_id: Mapped[str] = mapped_column(String(64), unique=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    email: Mapped[str] = mapped_column(String(255), default="")
    stats: Mapped[str] = mapped_column(String(32), default="underreview")
    advisor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entry_semester: Mapped[str] = mapped_column(String(64), default="")
    accept_form_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    letter_sent: Mapped[bool] = mapped_column(Boolean, default=False)


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (UniqueConstraint("edict_id", "user_id"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    edict_id: Mapped[str] = mapped_column(String(64), ForeignKey("edicts.id"))
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"))
    amount: Mapped[str] = mapped_column(String(16), default="0")


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    submission_id: Mapped[str] = mapped_column(String(64), ForeignKey("submissions.id"))
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(DateTime)
    start_date: Mapped[str | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[str | None] = mapped_column(DateTime, nullable=True)


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "submission_id"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"))
    submission_id: Mapped[str] = mapped_column(String(64), ForeignKey("submissions.id"))


class Label(Base):
    __tablename__ = "labels"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"))
    submission_id: Mapped[str] = mapped_column(String(64), ForeignKey("submissions.id"))
    label: Mapped[str] = mapped_column(String(255))
    color: Mapped[str] = mapped_column(String(32), default="")
    context: Mapped[str] = mapped_column(String(32), default="candidate")


class PrivateNote(Base):
    __tablename__ = "private_notes"
    __table_args__ = (UniqueConstraint("user_id", "submission_id"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"))
    submission_id: Mapped[str] = mapped_column(String(64), ForeignKey("submissions.id"))
    note: Mapped[str] = mapped_column(Text, default="")


class SubmissionView(Base):
    __tablename__ = "submission_views"
    __table_args__ = (UniqueConstraint("user_id", "submission_id", "view_date"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"))
    submission_id: Mapped[str] = mapped_column(String(64), ForeignKey("submissions.id"))
    view_date: Mapped[str] = mapped_column(Date)


class Bidding(Base):
    __tablename__ = "biddings"
    __table_args__ = (UniqueConstraint("user_id", "submission_id"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"))
    submission_id: Mapped[str] = mapped_column(String(64), ForeignKey("submissions.id"))
    bidding: Mapped[str] = mapped_column(String(64), default="")


engine = create_async_engine(settings.prejanus_database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
