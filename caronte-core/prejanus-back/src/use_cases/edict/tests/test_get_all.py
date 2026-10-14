import pytest

from src.use_cases.edict.get_all import EdictSchema, get_all_edicts

pytestmark = pytest.mark.anyio


async def test_get_all_edicts_returns_empty_list_when_no_edicts_are_found(session):
    edicts = await get_all_edicts(session)

    assert edicts == []


@pytest.mark.usefixtures("an_edict", "another_edict")
async def test_get_all_edicts_return_list_of_all_edicts(session):
    edicts = await get_all_edicts(session)

    assert len(edicts) == 2
    assert isinstance(edicts[0], EdictSchema)

    assert edicts[0].title == "Um edital de mestrado"
    assert edicts[0].year == 2024
    assert edicts[0].semester == 1
    assert edicts[0].edict_type == "Mestrado"
    assert edicts[0].is_open is True

    assert edicts[1].title == "Um edital passado de doutorado"
    assert edicts[1].year == 2023
    assert edicts[1].semester == 2
    assert edicts[1].edict_type == "Doutorado"
    assert edicts[1].is_open is False


@pytest.mark.usefixtures("an_edict", "another_edict")
async def test_get_all_edicts_return_list_of_edicts_filtered_by_type(session):
    edicts = await get_all_edicts(session, type="Mestrado")

    assert len(edicts) == 1
    assert edicts[0].title == "Um edital de mestrado"
    assert edicts[0].year == 2024
    assert edicts[0].semester == 1
    assert edicts[0].edict_type == "Mestrado"
    assert edicts[0].is_open is True


@pytest.mark.usefixtures("an_edict", "another_edict")
async def test_get_all_edicts_return_list_of_edicts_filtered_by_open_or_close_status(session):
    edicts = await get_all_edicts(session, is_open=False)

    assert len(edicts) == 1
    assert edicts[0].title == "Um edital passado de doutorado"
    assert edicts[0].year == 2023
    assert edicts[0].semester == 2
    assert edicts[0].edict_type == "Doutorado"
    assert edicts[0].is_open is False

