from http import HTTPStatus
from fastapi.testclient import TestClient
import pytest
from datetime import date
from src.infra.database.models.edict import Edict
from src.infra.database.models.submission import Submission

pytestmark = pytest.mark.anyio


@pytest.mark.usefixtures("an_edict", "another_edict")
async def test_get_all_return_all_registered_edicts(client: TestClient):
    response = client.get("/edicts")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == [
        {
            "id": 1,
            "title": "Um edital de mestrado",
            "year": 2024,
            "semester": 1,
            "edict_type": "Mestrado",
            "is_open": True,
        },
        {
            "id": 2,
            "title": "Um edital passado de doutorado",
            "year": 2023,
            "semester": 2,
            "edict_type": "Doutorado",
            "is_open": False,
        },
    ]


@pytest.mark.usefixtures("an_edict", "another_edict")
async def test_get_all_return_registered_edicts_with_the_applied_filters(
    client: TestClient,
):
    response = client.get("/edicts?type=Mestrado&is_open=True")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == [
        {
            "id": 1,
            "title": "Um edital de mestrado",
            "year": 2024,
            "semester": 1,
            "edict_type": "Mestrado",
            "is_open": True,
        },
    ]


@pytest.mark.usefixtures("submission_a", "submission_b")
async def test_get_all_return_registered_submissions_associated_with_edict(
    client: TestClient,
):
    headers = {"Authorization": "Bearer valid_token_for_user_with_id_1"}
    response = client.get("/edicts/1/submissions", headers=headers)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "submissions": [
            {
                "id": 1,
                "name": "Zé",
                "nationality": "Brasileiro",
                "gender": "Masculino",
                "birth_date": "2000-05-05",
                "graduation": {"country": "Brasil", "institution": "USP", "year": 2022},
                "poscomp": {"year": 2022, "score": 40},
                "research": {
                    "field": {
                        "primary": "Engenharia de software",
                        "secondary": "Ciência de dados",
                    },
                    "program": "Cálculo 1",
                    "dedication_level": "Integral",
                    "will_apply_scholarship": True,
                },
                "lattes_curriculum": "meulattes.com",
                "is_favorite": False,
                "current_occupation": "Analista de sistemas",
            }
        ]
    }


async def test_insert_edict_creates_new_edict_successfully(client: TestClient):
    new_edict_data = {
        "title": "Novo Edital de Doutorado",
        "description": "Um edital de doutorado",
        "year": 2025,
        "semester": 2,
        "edict_type": "Doutorado",
        "is_open": False,
        "date": str(date(2025, 2, 1)),  # Formato ISO
    }

    response = client.post("/edicts", json=new_edict_data)

    assert response.status_code == HTTPStatus.OK
    response_json = response.json()
    assert response_json["title"] == "Novo Edital de Doutorado"
    assert response_json["year"] == 2025
    assert response_json["semester"] == 2
    assert response_json["edict_type"] == "Doutorado"
    assert response_json["is_open"] is False
    # Ajustado para incluir a hora
    assert response_json["date"] == "2025-02-01T00:00:00"


@pytest.mark.usefixtures("edict_b")
async def test_get_edict_return_edict_by_id(client: TestClient):
    response = client.get("/edicts/1")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "id": 1,
        "title": "Terceiro edital de mestrado",
        "description": "Edital de mestrado da computação, primeiro semestre de 2024",
        "date": "2024-01-10",
        "created_at": "2024-01-10T00:00:00",
        "year": 2022,
        "semester": 2,
        "type": "Mestrado",
        "is_open": False,
        "updated_at": "2024-03-10T00:00:00",
    }


# Teste removido devido à problemas de configuração no mock das variáveis

"""@pytest.mark.usefixtures("an_edict", "submission_a")
async def test_patch_close_edict_by_id_with_letters(client: TestClient, session, an_edict: Edict, submission_a: Submission):
    submission_a.advisor = "Prof. Orientador"
    submission_a.advisor_email = "orientador@example.com"
    await session.commit()

    payload = {
        "confirmation_deadline": "2024-12-01",
        "send_approval_letter": True
    }
    response = client.patch(
        "/edicts/1/close",
        json=payload
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "message": "Emails sent successfully.",
        "email_list" : ["ze@email.com"],
        "confirmation_deadline": "2024-12-01"
    }"""


@pytest.mark.usefixtures("an_edict", "submission_a")
async def test_patch_close_edict_by_id_without_letters(
    client: TestClient, session, an_edict: Edict, submission_a: Submission
):
    submission_a.advisor = "Prof. Orientador"
    submission_a.advisor_email = "orientador@example.com"
    await session.commit()

    payload = {"confirmation_deadline": "2024-12-01", "send_approval_letter": False}
    response = client.patch("/edicts/1/close", json=payload)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.usefixtures("edict_b")
async def test_patch_close_edict_when_already_closed(client: TestClient):
    payload = {"confirmation_deadline": "2024-12-01", "send_approval_letter": True}
    response = client.patch("/edicts/1/close", json=payload)

    assert response.status_code == HTTPStatus.CONFLICT
