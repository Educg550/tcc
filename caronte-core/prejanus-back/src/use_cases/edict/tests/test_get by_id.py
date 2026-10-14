import pytest
from datetime import date, datetime
from src.use_cases.edict.get_by_id import EdictByIdSchema, get_edict_by_id

pytestmark = pytest.mark.anyio

@pytest.mark.usefixtures("edict_b")
async def test_get_edict_by_id_return_edict(session):
    edict = await get_edict_by_id(session, edict_id=1)

    assert isinstance(edict, EdictByIdSchema)

    assert edict.id == 1
    assert edict.title =="Terceiro edital de mestrado"
    assert edict.description == "Edital de mestrado da computação, primeiro semestre de 2024"
    assert edict.closed_date == date.fromisoformat("2024-01-10")
    assert edict.created_at == datetime.fromisoformat("2024-01-10")
    assert edict.year == 2022
    assert edict.semester == 2
    assert edict.type == "Mestrado"
    assert not edict.is_open
    assert edict.updated_at == datetime.fromisoformat("2024-03-10")