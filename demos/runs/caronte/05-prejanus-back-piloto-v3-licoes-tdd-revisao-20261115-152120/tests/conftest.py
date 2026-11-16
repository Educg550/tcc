import pytest

from helpers import client


def _fixture(var):
    @pytest.fixture(scope="session")
    def _c():
        with client(var) as c:
            yield c

    return _c


api = _fixture("CARONTE_API")
admin = _fixture("CARONTE_API_ADMIN")
outro = _fixture("CARONTE_API_OUTRO")
secretaria = _fixture("CARONTE_API_SECRETARIA")
coordenador = _fixture("CARONTE_API_COORDENADOR")
estudante = _fixture("CARONTE_API_ESTUDANTE")
senhaunica = _fixture("CARONTE_API_SENHAUNICA")
sem_atalho = _fixture("CARONTE_API_SEM_ATALHO")
