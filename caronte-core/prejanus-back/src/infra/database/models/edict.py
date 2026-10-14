from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


from src.infra.database.models.base import Base
if TYPE_CHECKING:
    from src.infra.database.models.submission import Submission
    from src.infra.database.models.edict_phase import EdictPhase
    from src.infra.database.models.user_edict_slots import UserEdictSlots
    from src.infra.database.models.edict_form_mapping import EdictFormMapping
    from src.infra.database.models.user import User
                



class Edict(Base):
    __tablename__ = 'edict'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    candidate_forms: Mapped[str] = mapped_column(String, nullable=True)
    recommenders_forms: Mapped[str] = mapped_column(String, nullable=True)
    accept_forms: Mapped[str] = mapped_column(String, nullable=True)
    closed_date: Mapped[date] = mapped_column(Date, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    phase: Mapped[str] = mapped_column(String, default="inscricoes", nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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

    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('user.id', 
        ondelete='CASCADE')
        )
    user: Mapped['User'] = relationship(
        'User',
        back_populates='edicts'
    )
    submissions: Mapped[list['Submission']] = relationship(
        'Submission',
        back_populates='edict',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    edict_phases: Mapped[list['EdictPhase']] = relationship(
        'EdictPhase', 
        back_populates='edict', 
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    users_with_slots: Mapped[list['UserEdictSlots']] = relationship(
        'UserEdictSlots',
        back_populates='edict',
        cascade='all, delete-orphan'
    )
    form_mappings: Mapped[list["EdictFormMapping"]] = relationship(
        "EdictFormMapping",
        back_populates="edict",
        cascade="all, delete-orphan"
    )
