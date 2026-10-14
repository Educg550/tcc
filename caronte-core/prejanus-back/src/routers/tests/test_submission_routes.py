from http import HTTPStatus
from fastapi.testclient import TestClient
import pytest
from src.infra.database.models.submission import Submission
from src.infra.database.models.user import User

pytestmark = pytest.mark.anyio



@pytest.mark.usefixtures("submission_a", "submission_b")
async def test_get_all_submissions_return_list_of_all_submissions(client: TestClient):
    response = client.get("/submissions")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"submissions": [
        {
            "id": 1,
            "name": "Zé",
            "nationality": "Brasileiro",
            "gender": "Masculino",
            "birth_date": "2000-05-05",
            "graduation": {
                "country": "Brasil",
                "institution": "USP",
                "year": 2022
            },
            "poscomp": {
                "year": 2022,
                "score": 40
            },
            "current_occupation": "Analista de sistemas",
            "research": {
                "program":"Cálculo 1",
                "field": {
                    "primary": "Engenharia de software",
                    "secondary": "Ciência de dados"
                },
                "dedication_level": "Integral",
                "will_apply_scholarship": True,
            },
            "is_favorite": False,
            "comments": [],
            "documents": ["http://lattes.com"]
        },
        {
            "id": 2,
            "name": "Mário",
            "nationality": "Brasileiro",
            "gender": "Masculino",
            "birth_date": "1980-05-05",
            "graduation": {
                "country": "Brasil",
                "institution": "USP",
                "year": 2022
            },
            "poscomp": {
                "year": 2022,
                "score": 15
            },
            "current_occupation": "",
             "research": {
                "program":  "Deep Learning",
                "field": {
                    "primary": "IA",
                    "secondary": "Computação musical"
                },
                "dedication_level": "Parcial",
                "will_apply_scholarship": False,
            },
            "is_favorite": False,
            "comments": [],
            "documents": []
        },
    ]}

@pytest.mark.usefixtures("submission_a", "user_a")
async def test_post_comment_to_submission(client: TestClient):
    # Definindo os dados do comentário
    headers = {
        "Authorization": "Bearer valid_token_for_user_with_id_1"
    }
    comment_data = {
        "comment": "Este é um novo comentário."
    }

    # Enviando o POST request para adicionar o comentário
    response = client.post("/submissions/1/comments", headers=headers, json=comment_data)

    # Verificando se o status code é 201 (Created)
    assert response.status_code == HTTPStatus.OK 

    # Verificando se o comentário retornado é o mesmo enviado
    print(response.json())
    assert response.json() == {
        "id": 1,  # O ID do comentário pode variar dependendo dos dados no banco
        "user": {
            "id": 1,
            "name": "Test User",
        },
        "submission_id": 1,
        "comment": "Este é um novo comentário.",
        "created_at": response.json().get("created_at"),
        "updated_at": None  # Comentário recém criado não deve ter updated_at
    }

@pytest.mark.usefixtures("submission_a", "user_a")
async def test_delete_comment(client: TestClient):
    # Definindo os dados do comentário
    headers = {
        "Authorization": "Bearer valid_token_for_user_with_id_1"
    }
    comment_data = {
        "comment": "Este é um novo comentário."
    }

    # Adicionando um comentário para depois deletá-lo
    response = client.post("/submissions/1/comments", headers=headers, json=comment_data)
    assert response.status_code == HTTPStatus.OK 
    comment_id = response.json()["id"]

    # Deletando o comentário
    delete_response = client.delete(f"/submissions/comments/{comment_id}", headers=headers)
    assert delete_response.status_code == HTTPStatus.NO_CONTENT



@pytest.mark.usefixtures("submission_a")
async def test_get_submission_by_id_return_error_when_submission_is_not_found(client: TestClient):
    headers = {
        "Authorization": "Bearer valid_token_for_user_with_id_1"
    }
    response = client.get("/submissions/3", headers=headers)
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.usefixtures("submission_a", "submission_b")
async def test_get_submission_by_id_return_submission_with_it_details(client: TestClient):
    headers = {
        "Authorization": "Bearer valid_token_for_user_with_id_1"
    }
    response = client.get("/submissions/1", headers=headers)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "id": 1,
        "name": "Zé",
        "nationality": "Brasileiro",
        "gender": "Masculino",
        "birth_date": "2000-05-05",
        "graduation": {
            "year": 2022,
            "institution": "USP",
            "country": "Brasil"
        },
        "poscomp": {
            "year": 2022,
            "score": 40
        },
        "current_occupation": "Analista de sistemas",
        "research": {
            "program": "Cálculo 1",
            "field": {
                "primary": "Engenharia de software",
                "secondary": "Ciência de dados"
            },
            "dedication_level": "Integral",
            "will_apply_scholarship": True
        },
        "is_favorite": False,
        "documents": [
            {
                "title": "Boletim POSCOMP",
                "url": None
            },
            {
                "title": "Currículo Lattes",
                "url": "http://lattes.com"
            },
            {
                "title": "Carta de motivação",
                "url": None
            },
            {
                "title": "Histórico da graduação",
                "url": None
            }
        ],
        "comments": []
    }


#Favorites
@pytest.mark.usefixtures("user_a", "submission_a")  
async def test_create_favorite_success(client: TestClient, user_a: User, submission_a: Submission):
    headers = {
        "Authorization": "Bearer valid_token_for_user_with_id_1"
    }
    
    response = client.post(f"/submissions/{submission_a.id}/favorites", headers=headers)
    
    assert response.status_code == 201  
    assert response.content == b""  


@pytest.mark.usefixtures("user_a", "submission_a") 
async def test_create_favorite_submission_not_found(client: TestClient, user_a: User):
    headers = {
        "Authorization": "Bearer valid_token_for_user_with_id_1"
    }
    
    response = client.post(f"/submissions/{999}/favorites", headers=headers)
    
    assert response.status_code == 404 
    assert response.json() == {"detail": "Submission with ID 999 was not found."}


@pytest.mark.usefixtures("user_a", "submission_a")  
async def test_create_favorite_already_exists(client: TestClient, user_a: User, submission_a: Submission):
    headers = {
        "Authorization": "Bearer valid_token_for_user_with_id_1"
    }
    
    client.post(f"/submissions/{submission_a.id}/favorites", headers=headers)
    
    response = client.post(f"/submissions/{submission_a.id}/favorites", headers=headers)
    
    assert response.status_code == 409  
    assert response.json() == {"detail": f"Favorite for User ID {user_a.id} and Submission ID {submission_a.id} already exists."}

@pytest.mark.usefixtures("user_a")
async def test_delete_favorite_success(client: TestClient, submission_a: Submission):
    headers = {
        "Authorization": "Bearer valid_token_for_user_with_id_1"
    }
    
    client.post(f"/submissions/{submission_a.id}/favorites", headers=headers)
    response = client.delete(f"/submissions/{submission_a.id}/favorites", headers=headers)

    assert response.status_code == 204 
    assert response.content == b""  

@pytest.mark.usefixtures("user_a", "submission_a")
async def test_delete_favorite_not_found(client: TestClient, user_a: User, submission_a: Submission):
    headers = {
        "Authorization": "Bearer valid_token_for_user_with_id_1"
    }
    
    response = client.delete(f"/submissions/{submission_a.id}/favorites", headers=headers)

    assert response.status_code == 404  
    assert response.json() == {"detail": f"Favorite with User ID {user_a.id} and Submission ID {submission_a.id} not found."}