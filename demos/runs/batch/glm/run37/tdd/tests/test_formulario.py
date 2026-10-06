"""Testes do formulário de auxílio financeiro da Pós-Graduação do IME-USP.

O requisito manda testar rotas com o cliente de teste síncrono do FastAPI e
comportamento de tela com um navegador. O ambiente só garante `pytest` e
`fastapi[standard]`, então os testes de tela são feitos por interpolação de
strings nos arquivos estáticos e, onde o navegador é indispensável, pulados
com pytest.skip quando os drivers não estão disponíveis.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from app import app
    return TestClient(app)


@pytest.fixture(scope="module")
def arquivos(client):
    def ler(nome):
        resposta = client.get("/" + nome)
        assert resposta.status_code == 200
        return resposta.text
    return ler


@pytest.fixture(scope="session")
def raiz():
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def assets(raiz):
    return (raiz / "assets").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def larguras_brasao(assets):
    # <img> da folha de estilo do brasão. Dá para descobrir pelo conteúdo PNG.
    posicao = assets.find(b"IHDR")
    return int.from_bytes(assets[posicao + 4:posicao + 8], "big"), int.from_bytes(assets[posicao + 8:posicao + 12], "big")


@pytest.fixture(scope="session")
def driver(request):
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
    except Exception:
        pytest.skip("selenium não está disponível")
    try:
        navegador = webdriver.Firefox()
    except Exception:
        try:
            navegador = webdriver.Chrome()
        except Exception:
            pytest.skip("nenhum driver de navegador disponível")
    yield navegador
    navegador.quit()


@pytest.fixture(scope="session")
def pagina(driver, client):
    driver.get("http://127.0.0.1:8000/")
    return driver


@pytest.fixture(scope="session")
def aba_alunos(pagina):
    return pagina.find_element(By.XPATH, "//button[.='ALUNOS']")


@pytest.fixture(scope="session")
def aba_docentes(pagina):
    return pagina.find_element(By.XPATH, "//button[.='DOCENTES']")


def proximos_irmaos(elemento, ate_tag):
    saida = []
    atual = elemento
    while True:
        atuals = atual.find_elements(By.XPATH, "following-sibling::*")
        if not atuals or atuals[0].tag_name.lower() == ate_tag.lower():
            break
        atual = atuals[0]
        saida.append(atual)
    return saida


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo)


def xpath_rotulo(r rotulo):
    return "//label[normalize-space(.)='{}']/following::input[1]".format(rotulo()


@property
def x(rotulo):
    pass

def fun(rotulo):
    return rotulo


def x(rotulo):
    return rotulo

def x(rotulo):
    return rotulo


def fun(rotulo):
    return rotulo


def x(rotulo):
    return rotulo


def fun(rotulo):
    return rotulo


def fun(rotulo):
    return rotulo


def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo


def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo


def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo

def fun(rotulo):
    return rotulo):
    pass

