import re

from conftest import ROTULOS_EM_ORDEM


def test_pagina_servida_no_raiz(cliente):
    resposta = cliente.get('/')
    assert resposta.status_code == 200
    assert 'text/html' in resposta.headers.get('content-type', '')


def test_arquivos_do_front_referenciados(pagina):
    pagina_em_minusculas = pagina.lower()
    assert 'style.css' in pagina_em_minusculas
    assert 'app.js' in pagina_em_minusculas


def test_aba_alunos_antes_da_aba_docentes(texto):
    assert 'alunos' in texto
    assert 'docentes' in texto
    assert texto.find('alunos') < texto.find('docentes')


def test_cada_formulario_tem_seu_botao_enviar(texto):
    assert texto.count('enviar solicitação') == 2


def test_rotulos_e_blocos_na_ordem(texto):
    posicao = 0
    for rotulo in ROTULOS_EM_ORDEM:
        achou = texto.find(rotulo, posicao)
        assert achou != -1, 'rótulo ausente ou fora de ordem: %r' % rotulo
        posicao = achou + 1


def test_opcoes_das_selecoes(texto, js):
    tela = texto + js.lower()
    for opcao in ('mestrado', 'doutorado', 'participação em evento',
                  'banca de exame ou defesa', 'outro', 'pôster',
                  'apresentação oral', 'outra', 'não irá apresentar trabalho'):
        assert opcao in tela, 'opção ausente: %s' % opcao


def test_cabecalho_institucional(texto, pagina):
    assert 'universidade de são paulo' in texto
    assert 'usp-logo.png' in pagina


def test_logotipo_servido_como_estatico(cliente, pagina):
    achou = re.search(r"[\"']([^\"']*usp-logo\.png)[\"']", pagina)
    assert achou, 'a página não referencia assets/usp-logo.png'
    caminho = achou.group(1)
    if not caminho.startswith('/'):
        caminho = '/' + caminho
    assert cliente.get(caminho).status_code == 200


def test_nenhuma_imagem_alem_do_logotipo(pagina):
    referencias = re.findall(
        r"[\"'(]([^\"')]*\.(?:png|jpe?g|svg|gif|webp))[\"')"]", pagina, re.I)
    assert referencias, 'a página não referencia nenhuma imagem'
    for referencia in referencias:
        assert 'usp-logo' in referencia.lower(), (
            'imagem estranha ao cabeçalho: %s' % referencia)


def test_titulo_da_confirmacao_na_tela(texto, js):
    assert 'solicitação registrada' in texto + js.lower()


def test_todo_campo_de_digitacao_tem_placeholder(pagina):
    tags = re.findall(r'<(?:input|textarea)\b[^>]*>', pagina, re.I)
    campos = []
    for tag in tags:
        tipo = re.search(r"type=[\"']([a-z0-9]+)[\"']", tag, re.I)
        if tag.lower().startswith('<textarea'):
            campos.append(tag)
        elif tipo is None or tipo.group(1).lower() in ('text', 'email', 'tel', 'number'):
            campos.append(tag)
    assert len(campos) >= 50, 'faltam campos de digitação nas duas abas'
    sem_placeholder = [tag for tag in campos if 'placeholder' not in tag.lower()]
    assert not sem_placeholder, '%d campos sem placeholder' % len(sem_placeholder)


def test_placeholder_nao_repete_o_rotulo(pagina):
    valores = re.findall(r"placeholder=[\"']([^\"']+)[\"']", pagina, re.I)
    assert valores
    rotulos = {rotulo.lower() for rotulo in ROTULOS_EM_ORDEM}
    for valor in valores:
        assert valor.strip().lower() not in rotulos, (
            'placeholder repete o rótulo: %s' % valor)


def test_folha_de_estilo_tem_as_cores_da_usp(css):
    folha = css.lower()
    assert '#1094ab' in folha
    assert '#fcb421' in folha or '#64c4d2' in folha


def test_fonte_da_identidade(css):
    folha = css.lower()
    assert 'open sans' in folha or 'sans-serif' in folha


def test_nenhum_recurso_vem_da_rede(pagina, css):
    assert 'fonts.googleapis' not in pagina.lower()
    assert 'fonts.googleapis' not in css.lower()
    assert 'http://' not in css.lower()
    assert 'https://' not in css.lower()
