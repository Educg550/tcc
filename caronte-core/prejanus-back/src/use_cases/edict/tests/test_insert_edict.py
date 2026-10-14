import pytest
from datetime import datetime
from sqlalchemy import text
from src.use_cases.edict.insert_edict import InsertEdictSchema, insert_edict

pytestmark = pytest.mark.anyio


async def test_insert_edict_inserts_an_edict_successfully(session):
    edict_data = InsertEdictSchema(
        title="Novo Edital de Mestrado",
        description="Descrição teste",
        year=2024,
        semester=1,
        edict_type="Mestrado",
        is_open=True,
        closed_date=datetime.now(),
    )

    inserted_edict = await insert_edict(session, edict_data)

    assert inserted_edict.id == 1
    assert inserted_edict.title == "Novo Edital de Mestrado"
    assert inserted_edict.description == "Descrição teste"
    assert inserted_edict.year == 2024
    assert inserted_edict.semester == 1
    assert inserted_edict.edict_type == "Mestrado"
    assert inserted_edict.is_open is True
    assert inserted_edict.date is not None


'''async def test_insert_edict_with_duplicate_id_fails(session):
    edict_data = EdictSchema(
        # id=1,
        title="Edital Duplicado",
        description="Descrição teste",
        year=2024,
        semester=1,
        edict_type="Mestrado",
        is_open=True,
        closed_date=datetime.now()
    )

    # Primeiro insert deve funcionar
    await insert_edict(session, edict_data)

    # Tentar inserir um edital com o mesmo ID deve gerar uma exceção
    with pytest.raises(Exception):
        await insert_edict(session, edict_data)'''


@pytest.mark.usefixtures("an_edict")
async def test_insert_edict_increases_edict_count(session):
    initial_query = await session.execute(text("SELECT COUNT(*) FROM edict"))
    initial_count = initial_query.scalar()

    edict_data = InsertEdictSchema(
        # id=2,
        title="Edital de Doutorado",
        description="Descrição teste",
        year=2025,
        semester=2,
        edict_type="Doutorado",
        is_open=False,
        closed_date=datetime.now()
    )

    await insert_edict(session, edict_data)

    final_query = await session.execute(text("SELECT COUNT(*) FROM edict"))
    final_count = final_query.scalar()

    assert final_count == initial_count + 1
