import re

from ambiente import RAIZ

REQUISITO = RAIZ / "demos/requisitos/03-caronte-prejanus-completo/requisito.md"
# Avaliados na etapa final do CUA, não pela suíte HTTP (avaliacao.md).
PENDENTES = {"V2-INT-01", "V2-INT-03"}


def test_todo_requisito_tem_teste(request):
    ids = set(re.findall(r"^### (V2-[A-Z]+-\d+)", REQUISITO.read_text(), re.M))
    citados = {i for item in request.session.items for m in item.iter_markers("req") for i in m.args}
    assert ids - citados == PENDENTES
    assert citados - ids == set()
