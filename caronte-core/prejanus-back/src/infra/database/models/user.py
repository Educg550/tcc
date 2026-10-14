from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.database.models.base import Base

if TYPE_CHECKING:
    from src.infra.database.models.submission import Submission
    from src.infra.database.models.favorites import Favorites
    from src.infra.database.models.comment import Comment
    from src.infra.database.models.labels import Labels
    from src.infra.database.models.edict_form_mapping import EdictFormMapping
    from src.infra.database.models.edict import Edict
    from src.infra.database.models.private_note import PrivateNote
    from src.infra.database.models.user_edict_slots import UserEdictSlots
    from src.infra.database.models.submission_view import SubmissionView

class RolesEnum(Enum):
    TEACHER = "teacher"
    COORDINATOR = "coordinator"
    STUDENT = "student"
    ADMINISTRATOR = "administrator"
    SECRETARY = "secretary"

class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    nusp: Mapped[str] = mapped_column(String, nullable=True)
    research_field: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(tz=timezone.utc), 
        nullable=True
    )

    submissions_as_advisor: Mapped[list['Submission']] = relationship(
        'Submission', 
        back_populates='advisor'
    )
    favorites: Mapped[list['Favorites']] = relationship(
        'Submission',
        secondary='favorites',
        back_populates='favorited_by'
    )
    edicts: Mapped[list['Edict']] = relationship(
        'Edict',
        back_populates='user',
        cascade='all, delete-orphan'
    )
    edict_form_mappings: Mapped[list['EdictFormMapping']] = relationship(
        'EdictFormMapping',
        back_populates='user',
        cascade='all, delete-orphan'
    )
    comments: Mapped[list['Comment']] = relationship(
        'Comment', back_populates='user'
    )
    labels: Mapped[list['Labels']] = relationship(
        'Labels', back_populates='user'
    )
    private_notes: Mapped[list["PrivateNote"]] = relationship(
        "PrivateNote", back_populates="user"
    )
    edicts_with_slots: Mapped[list['UserEdictSlots']] = relationship(
        'UserEdictSlots',
        back_populates='user',
        cascade='all, delete-orphan'
    )
    views: Mapped[list["SubmissionView"]] = relationship(
        "SubmissionView",
        back_populates="user",
        cascade="all, delete-orphan"
    )
