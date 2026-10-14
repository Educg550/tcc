from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    DateTime,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.database.models.base import Base

from sqlalchemy import Enum

from src.infra.database.models.user import User

FormTypeEnum = Enum("candidate", "recommender", name="form_type_enum")


# O EdictFormMapping cria mapeamentos entre dados que o Prejanus precisa e dados que o Form oferece.
# Ou seja, teríamos uma realocação de responsabilidades: em vez de o Prejanus criar o mapeamento,
# a pessoa que estaria criando o edital se responsabilizaria pela criação.
class EdictFormMapping(Base):
    __tablename__ = "edict_form_mappings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    edict_id: Mapped[int] = mapped_column(
        ForeignKey("edict.id", ondelete="CASCADE"), nullable=False
    )
    form_id: Mapped[str] = mapped_column(
        String, nullable=True
    )  # Um edital pode ter vários formulários (submissão, recomendação, etc)

    form_type: Mapped[str] = mapped_column(
        FormTypeEnum, nullable=False
    )  # "candidate" ou "recommender"

    # Podem existir mapeamentos para diferentes tipos de versões do formulário,
    # evitando que submissões antigas "quebrem"
    form_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # O mapeamento será armazenado como um JSON
    mapping: Mapped[dict] = mapped_column(JSONB, nullable=False)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE")
    )
    user: Mapped["User"] = relationship("User", back_populates="edict_form_mappings")

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    edict = relationship("Edict", back_populates="form_mappings")

    __table_args__ = (
        UniqueConstraint(
            "edict_id",
            "form_type",
            "form_version",
        ),
    )
