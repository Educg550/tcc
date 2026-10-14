from __future__ import annotations
from datetime import date
from typing import TYPE_CHECKING


from sqlalchemy import Date, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


from src.infra.database.models.base import Base

if TYPE_CHECKING:
    from src.infra.database.models.edict import Edict

class EdictPhase(Base):
    __tablename__ = 'edict_phase'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    edict_id: Mapped[int] = mapped_column(ForeignKey('edict.id', ondelete='CASCADE'))
    closed_date: Mapped[date] = mapped_column(Date, nullable=True)
    phase: Mapped[str] = mapped_column(String, nullable=False)

    edict: Mapped['Edict'] = relationship('Edict', back_populates='edict_phases')