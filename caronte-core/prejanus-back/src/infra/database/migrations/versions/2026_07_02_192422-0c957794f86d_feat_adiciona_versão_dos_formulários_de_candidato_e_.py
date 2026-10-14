"""feat: adiciona versão dos formulários de candidato e recomendador em submissão

Revision ID: 0c957794f86d
Revises: d54dfef0cea7
Create Date: 2026-07-02 19:24:22.314816+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0c957794f86d"
down_revision: Union[str, None] = "d54dfef0cea7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "edict_form_mappings",
        sa.Column(
            "form_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    op.drop_constraint(
        op.f("edict_form_mappings_edict_id_form_type_version_key"),
        "edict_form_mappings",
        type_="unique",
    )

    op.create_unique_constraint(
        "edict_form_mappings_edict_id_form_type_form_version_key",
        "edict_form_mappings",
        ["edict_id", "form_type", "form_version"],
    )

    op.drop_column("edict_form_mappings", "version")

    op.add_column(
        "submission",
        sa.Column(
            "recommender_form_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    op.add_column(
        "submission",
        sa.Column(
            "candidate_form_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    op.drop_column("submission", "form_version")

    # Remove o server_default, deixando apenas o default do ORM
    op.alter_column(
        "edict_form_mappings",
        "form_version",
        server_default=None,
    )

    op.alter_column(
        "submission",
        "recommender_form_version",
        server_default=None,
    )

    op.alter_column(
        "submission",
        "candidate_form_version",
        server_default=None,
    )


def downgrade() -> None:
    op.add_column(
        "submission",
        sa.Column(
            "form_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    op.drop_column("submission", "candidate_form_version")
    op.drop_column("submission", "recommender_form_version")

    op.add_column(
        "edict_form_mappings",
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    op.drop_constraint(
        "edict_form_mappings_edict_id_form_type_form_version_key",
        "edict_form_mappings",
        type_="unique",
    )

    op.create_unique_constraint(
        "edict_form_mappings_edict_id_form_type_version_key",
        "edict_form_mappings",
        ["edict_id", "form_type", "version"],
    )

    op.drop_column("edict_form_mappings", "form_version")

    op.alter_column(
        "submission",
        "form_version",
        server_default=None,
    )

    op.alter_column(
        "edict_form_mappings",
        "version",
        server_default=None,
    )
