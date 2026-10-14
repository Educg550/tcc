from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.database.models.base import Base
if TYPE_CHECKING:
    from src.infra.database.models.submission import Submission
    from src.infra.database.models.user import User

class Labels(Base):
    __tablename__ = 'labels'

    id: Mapped[int] = mapped_column(
        primary_key=True, 
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('user.id', ondelete='CASCADE')
    )
    submission_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('submission.id', ondelete='CASCADE')
    )
    label: Mapped[str] = mapped_column(String, nullable=False)
    color: Mapped[str] = mapped_column(String, nullable=False)

    context_type: Mapped[str] = mapped_column(String, nullable=True)

    submission: Mapped['Submission'] = relationship(
        'Submission', back_populates='labels'
    )
    user: Mapped['User'] = relationship(
        'User', back_populates='labels'
    )
