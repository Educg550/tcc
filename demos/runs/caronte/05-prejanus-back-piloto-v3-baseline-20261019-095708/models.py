from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    nusp = Column(String)
    research_field = Column(String)
    created_at = Column(DateTime(timezone=True))


class Edict(Base):
    __tablename__ = "edict"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    candidate_forms = Column(String)
    recommenders_forms = Column(String)
    closed_date = Column(Date, nullable=False)
    year = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    edict_type = Column("type", String, nullable=False)
    phase = Column(String, nullable=False)
    is_open = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    accept_forms = Column(String)
    user_id = Column(Integer, ForeignKey("user.id"))

    phases = relationship(
        "EdictPhase", cascade="all, delete", passive_deletes=True, order_by="EdictPhase.id"
    )


class EdictPhase(Base):
    __tablename__ = "edict_phase"

    id = Column(Integer, primary_key=True)
    edict_id = Column(Integer, ForeignKey("edict.id", ondelete="CASCADE"), nullable=False)
    closed_date = Column(Date)
    phase = Column(String, nullable=False)


class EdictFormMapping(Base):
    __tablename__ = "edict_form_mappings"

    id = Column(Integer, primary_key=True)
    edict_id = Column(Integer, ForeignKey("edict.id", ondelete="CASCADE"), nullable=False)
    form_type = Column(String, nullable=False)
    mapping = Column(JSON, nullable=False)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    form_id = Column(String)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    form_version = Column(Integer, nullable=False)


class Submission(Base):
    __tablename__ = "submission"

    id = Column(Integer, primary_key=True)
    edict_id = Column(Integer, ForeignKey("edict.id", ondelete="CASCADE"), nullable=False)
    advisor_id = Column(Integer, ForeignKey("user.id"))
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    candidate_form_id = Column(Integer, nullable=False)
    recommenders_form_ids = Column(JSON)
    stats = Column(String, nullable=False, default="underreview")
    accept_form_id = Column(Integer)
    entry_semester = Column(String)
    letter_sent = Column(Boolean, nullable=False, default=False)
    recommender_form_version = Column(Integer, nullable=False)
    candidate_form_version = Column(Integer, nullable=False)


class Comment(Base):
    __tablename__ = "comment"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    submission_id = Column(Integer, ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)
    comment = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))


class Favorite(Base):
    __tablename__ = "favorites"

    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    submission_id = Column(Integer, ForeignKey("submission.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class Label(Base):
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    submission_id = Column(Integer, ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)
    label = Column(String, nullable=False)
    color = Column(String, nullable=False)
    context_type = Column(String)


class PrivateNote(Base):
    __tablename__ = "private_note"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    submission_id = Column(Integer, ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)
    note = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True))


class SubmissionView(Base):
    __tablename__ = "submission_view"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    submission_id = Column(Integer, ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))


class UserEdictSlot(Base):
    __tablename__ = "user_edict_slots"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    edict_id = Column(Integer, ForeignKey("edict.id", ondelete="CASCADE"), nullable=False)
    slots = Column(Integer)
