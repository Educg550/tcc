from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    ForeignKey,
    UniqueConstraint,
    JSON,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.database.models.base import Base

if TYPE_CHECKING:
    from src.infra.database.models.edict import Edict
    from src.infra.database.models.user import User
    from src.infra.database.models.comment import Comment
    from src.infra.database.models.private_note import PrivateNote
    from src.infra.database.models.labels import Labels
    from src.infra.database.models.submission_view import SubmissionView


class StatsEnum(Enum):
    APPROVED = "approved"
    REFUSED = "refused"
    UNDERREVIEW = "underreview"
    WAITLIST = "waitlist"


class Submission(Base):
    __tablename__ = "submission"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    edict_id: Mapped[int] = mapped_column(ForeignKey("edict.id", ondelete="CASCADE"))
    advisor_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=lambda: datetime.now(tz=timezone.utc),
        nullable=True,
    )

    candidate_form_id: Mapped[int] = mapped_column(Integer, nullable=False)
    recommenders_form_ids: Mapped[list[int]] = mapped_column(JSON, nullable=True)
    accept_form_id: Mapped[int] = mapped_column(Integer, nullable=True)

    stats: Mapped[str] = mapped_column(
        String, nullable=False, default=StatsEnum.UNDERREVIEW
    )

    entry_semester: Mapped[str] = mapped_column(String, nullable=True)
    letter_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    advisor: Mapped["User"] = relationship(
        "User", back_populates="submissions_as_advisor"
    )
    edict: Mapped["Edict"] = relationship("Edict", back_populates="submissions")
    favorited_by: Mapped[list["User"]] = relationship(
        "User", secondary="favorites", back_populates="favorites"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="submission"
    )
    labels: Mapped[list["Labels"]] = relationship("Labels", back_populates="submission")
    private_notes: Mapped[list["PrivateNote"]] = relationship(
        "PrivateNote", back_populates="submission"
    )

    # Será usado para o controle de mapeamento
    recommender_form_version: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )
    candidate_form_version: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("candidate_form_id", "edict_id", name="single_form_for_edict"),
    )
    views: Mapped[list["SubmissionView"]] = relationship(
        "SubmissionView", back_populates="submission", cascade="all, delete-orphan"
    )
