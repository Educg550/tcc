from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.database.models.base import Base
from src.infra.database.models.edict import Edict
if TYPE_CHECKING:
    from src.infra.database.models.user import User


class UserEdictSlots(Base):
    __tablename__ = 'user_edict_slots'

    id: Mapped[int] = mapped_column( primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    edict_id: Mapped[int] = mapped_column(ForeignKey('edict.id', ondelete='CASCADE'), nullable=False)

    slots: Mapped[int] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'edict_id', name='uq_user_edict'),
    )

    user: Mapped['User'] = relationship(
        'User', back_populates='edicts_with_slots'
    )
    edict: Mapped['Edict'] = relationship(
        'Edict', back_populates='users_with_slots'
    )
