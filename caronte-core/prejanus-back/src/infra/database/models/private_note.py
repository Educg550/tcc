from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.database.models.base import Base
if TYPE_CHECKING:
    from src.infra.database.models.submission import Submission
    from src.infra.database.models.user import User

class PrivateNote(Base):
    __tablename__ = "private_note"
    __table_args__ = (
        UniqueConstraint("user_id", "submission_id", name="uq_user_submission_private_note"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    submission_id: Mapped[int] = mapped_column(ForeignKey("submission.id", ondelete="CASCADE"))
    note: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        onupdate=lambda: datetime.now(tz=timezone.utc), 
        nullable=True
    )
    submission: Mapped["Submission"] = relationship(
        "Submission", back_populates="private_notes"
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="private_notes"
    )