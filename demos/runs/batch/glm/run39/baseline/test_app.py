"""Testes do backend de solicitação de auxílio financeiro."""

from app import Solicitacao, _validar, solicitar


def base():
    return Solicitacao(
        perfil="alunos",
        nome="Maria Aparecida da Silva Santos",
        nusp="12345678",
        programa="Matemática",
        nivel="Mestrado",
        tipo_auxilio="Participação em evento",
        email="nome@usp.br",
        evento_nome="XVI Escola de Álgebra",
        evento_periodo="10 a 14 de julho de 2025",
        evento_cidade="São Paulo",
        evento_estado="SP",
        evento_pais="Brasil",
        evento_link="",
        valor_centavos=150000,
        detalhamento="Inscrição e diárias.",
        apresentacao="Pôster",
        endereco={
            "nascimento": "01/02/1980",
            "logradouro": "Rua do Matão",
            "numero": "1010",
            "complemento": "",
            "bairro": "Butantã",
            "cep": "05508-090",
            "cidade": "São Paulo",
            "estado": "SP",
        },
        pagamento={
            "cpf": "123.456.789-09",
            "rg": "12.345.678-9",
            "banco": "Banco do Brasil",
            "agencia": "1234",
            "conta": "12345-6-X",
        },
    )


def test_solicitacao_valida():
    r = solicitar(base())
    assert r["ok"] is True
    assert r["titulo"] == "Solicitação registrada"


def test_campo_faltando():
    s = base()
    s.nome = ""
    assert "Preencha todos os campos" in _validar(s)


def test_erros_multiplos():
    s = base()
    s.nusp = "12.34"
    s.agencia = "12-x"
    s.valor_centavos = 0
    s.email = "sem-arroba"
    s.cpf = "12.345.678-9"
    s.cep = "05508-0"
    s.endereco["nascimento"] = "01/02/19"
    erros = _validar(s)
    assert "N. USP deve conter apenas números" in erros
    assert "Número da agência deve conter apenas números" in erros
    assert "Valor solicitado deve ser maior que 0" in erros
    assert "E-mail inválido" in erros
    assert "CPF deve estar no formato 000.000.000-00" in erros
    assert "CEP deve estar no formato 00000-000" in erros
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros


def test_cpf_dvs_incorretos():
    s = base()
    s.cpf = "123.456.789-00"
    assert "CPF inválido" in _validar(s)


def test_data_inexistente():
    s = base()
    s.endereco["nascimento"] = "31/02/1980"
    assert "Data de nascimento inválida" in _validar(s)


def test_oficio_alunos():
    r = solicitar(base())
    oficio = r["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_oficio_docentes():
    s = base()
    s.perfil = "docentes"
    s.nivel = ""
    s.tipo_auxilio = ""
    r = solicitar(s)
    oficio = r["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática\n" in oficio


def test_oficio_campos_opcionais():
    s = base()
    s.evento_link = "https://www.ime.usp.br"
    s.endereco["complemento"] = "Sala 12"
    r = solicitar(s)
    assert "Link do evento: https://www.ime.usp.br" in r["oficio"]
    assert "Complemento: Sala 12" in r["oficio"]


def test_moeda():
    from app import _moeda
    assert _moeda(1500) == "R$ 15,00"
    assert _moeda(150000) == "R$ 1.500,00"
    assert _moeda(150000000) == "R$ 1.500.000,00"
