from __future__ import annotations
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.database.models.base import Base
if TYPE_CHECKING:
    from src.infra.database.models.submission import Submission
    from src.infra.database.models.user import User

class SubmissionView(Base):
    __tablename__ = 'submission_view'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('user.id', ondelete='CASCADE')
    )
    submission_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('submission.id', ondelete='CASCADE')
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(tz=timezone.utc), 
        nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        onupdate=lambda: datetime.now(tz=timezone.utc), 
        nullable=True
    )

    submission: Mapped['Submission'] = relationship(
        'Submission', back_populates='views'
    )

    user: Mapped['User'] = relationship(
        'User', back_populates='views' 
)
