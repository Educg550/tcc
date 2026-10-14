from __future__ import annotations
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.database.models.base import Base
if TYPE_CHECKING:
    from src.infra.database.models.user import User


class Favorites(Base):
    __tablename__ = 'favorites'

    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('user.id', ondelete='CASCADE'), 
        primary_key=True
    )
    submission_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('submission.id', ondelete='CASCADE'), 
        primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(tz=timezone.utc), 
        nullable=False
    )
    user: Mapped['User'] = relationship(
        'User', 
        viewonly=True,
        overlaps="favorited_by,favorites"
    )
