import pytest
import httpx

BASE_URL = "http://localhost:8083"


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL) as c:
        yield c


@pytest.fixture(scope="module")
def edict_id(client):
    r = client.get("/edicts")
    assert r.status_code == 200
    edicts = r.json()
    assert isinstance(edicts, list) and edicts
    return edicts[0]["id"]


@pytest.fixture(scope="module")
def submission(client, edict_id):
    r = client.get(f"/edicts/{edict_id}/submissions")
    assert r.status_code == 200
    body = r.json()
    submissions = body["submissions"]
    assert isinstance(submissions, list) and submissions
    return submissions[0]


@pytest.fixture(scope="module")
def submission_detail(client, submission):
    r = client.get(f"/submissions/{submission['id']}")
    assert r.status_code == 200
    return r.json()


def fields_by_name(submission_detail):
    fields = {}
    for section in submission_detail["submission_form"]:
        for field in section["fields"]:
            fields[field["name"]] = field
    return fields


# PIL-AUT-01


def test_root(client):
    assert client.get("/").status_code == 200


def test_auth_login_dev_user(client):
    r = client.get("/auth/login")
    assert r.status_code == 200
    user = r.json()
    for key in ("id", "name", "email", "nusp", "role"):
        assert key in user
        assert user[key] not in (None, "")


# PIL-DOC-01


def test_edicts_list(client):
    r = client.get("/edicts")
    assert r.status_code == 200
    edicts = r.json()
    assert isinstance(edicts, list) and edicts
    assert all("id" in e for e in edicts)


def test_edict_detail(client, edict_id):
    r = client.get(f"/edicts/{edict_id}")
    assert r.status_code == 200
    edict = r.json()
    assert str(edict["candidate_form_id"]).isdigit()


def test_edict_submissions(client, edict_id):
    r = client.get(f"/edicts/{edict_id}/submissions")
    assert r.status_code == 200
    submissions = r.json()["submissions"]
    assert submissions
    assert submissions[0]["name"]


def test_edict_submissions_no_duplicates(client, edict_id):
    first = client.get(f"/edicts/{edict_id}/submissions").json()["submissions"]
    second = client.get(f"/edicts/{edict_id}/submissions").json()["submissions"]
    ids_first = [s["id"] for s in first]
    ids_second = [s["id"] for s in second]
    assert ids_first == ids_second
    assert len(ids_second) == len(set(ids_second))


# PIL-DOC-02


def test_submission_summary(client, submission, submission_detail):
    summary = submission_detail["summary"]
    assert summary["name"] == submission["name"]
    assert summary["email"]


def test_submission_form_sections(client, submission_detail):
    form = submission_detail["submission_form"]
    assert isinstance(form, list) and form
    for section in form:
        assert isinstance(section["fields"], list)
        for field in section["fields"]:
            for key in ("id", "name", "label", "type", "value"):
                assert key in field


def test_submission_form_known_values(client, submission_detail):
    fields = fields_by_name(submission_detail)
    assert fields["fullname"]["value"] == "Ana Piloto Caronte"
    assert fields["mother-fullname"]["value"] == "Maria Piloto Caronte"
    assert fields["biological-sex"]["value"] == "Feminino"
    assert fields["disabilities"]["value"] == '["Declaro que me identifico como PCD."]'
    assert fields["website"]["value"] == "https://example.com/ana"
    assert fields["relevant-information"]["value"] == (
        "Informação adicional da fixture de consulta."
    )


def test_submission_form_poscomp_empty(client, submission_detail):
    fields = fields_by_name(submission_detail)
    assert not fields["grades-poscomp"]["value"]


def test_submission_form_ethnicity_race_out_of_mapping(client, submission_detail):
    assert "ethnicity-race" not in fields_by_name(submission_detail)


# PIL-DOC-03


def file_fields(submission_detail):
    return [
        f
        for f in fields_by_name(submission_detail).values()
        if f["type"] == "File" and f["value"]
    ]


def test_download_all_files(client, submission, submission_detail):
    files = file_fields(submission_detail)
    assert len(files) == 8
    contents = []
    for field in files:
        r = client.get(
            f"/submissions/{submission['id']}/files/{field['name']}/{field['value']}"
        )
        assert r.status_code == 200
        assert "attachment" in r.headers["content-disposition"]
        assert r.content.startswith(b"%PDF")
        contents.append(r.content)
    assert len(set(contents)) == 8


def test_download_rejects_filename_outside_answer(client, submission, submission_detail):
    field = file_fields(submission_detail)[0]
    r = client.get(
        f"/submissions/{submission['id']}/files/{field['name']}/nao-existe.pdf"
    )
    assert r.status_code >= 400


def test_download_rejects_path_outside_volume(client, submission, submission_detail):
    field = file_fields(submission_detail)[0]
    r = client.get(
        f"/submissions/{submission['id']}/files/{field['name']}/..%2F..%2Fetc%2Fpasswd"
    )
    assert r.status_code >= 400