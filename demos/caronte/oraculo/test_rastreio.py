import re

from dados import CARONTE


def test_todo_requisito_tem_teste(request):
    ids = set(re.findall(r"^### (PIL-[A-Z]+-\d+)", (CARONTE / "requisitos.md").read_text(), re.M))
    citados = {i for item in request.session.items for m in item.iter_markers("req") for i in m.args}
    assert ids - citados == set()
    assert citados - ids == set()
