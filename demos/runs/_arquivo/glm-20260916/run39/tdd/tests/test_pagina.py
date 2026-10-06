import re

TITULOS_BLOCOS = [
    'SOLICITANTE E EVENTO',
    'ENDEREÇO DO SOLICITANTE',
    'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
]

ROTULOS_COMUNS = [
    'NOME COMPLETO - SEM ABREVIAR',
    'N. USP',
    'PROGRAMA',
    'E-MAIL',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
    'PERÍODO DO EVENTO, EXAME OU DEFESA',
    'CIDADE DO EVENTO, EXAME OU DEFESA',
    'ESTADO DO EVENTO, EXAME OU DEFESA',
    'PAÍS DO EVENTO, EXAME OU DEFESA',
    'LINK DO EVENTO, EXAME OU DEFESA',
    'VALOR SOLICITADO (R$)',
    'DETALHAMENTO DO PEDIDO',
    'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
    'DATA DE NASCIMENTO',
    'LOGRADOURO',
    'NÚMERO',
    'COMPLEMENTO',
    'BAIRRO',
    'CEP',
    'CIDADE',
    'ESTADO',
    'CPF (SEPARADOS POR PONTOS E TRAÇO)',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',
    'NOME DO BANCO',
    'NÚMERO DA AGÊNCIA',
    'NÚMERO DA CONTA',
]

ROTULOS_DE_ALUNOS = ['NÍVEL', 'TIPO DE AUXÍLIO']

OPCOES = [
    'Mestrado',
    'Doutorado',
    'Participação em evento',
    'Banca de exame ou defesa',
    'Outro',
    'Pôster',
    'Apresentação oral',
    'Outra',
    'Não irá apresentar trabalho',
]


def _sem_aspas(texto):
    return texto.strip(chr(34)).strip(chr(39))


def _valores_de_atributo(pagina, padrao_da_tag, atributo):
    valores = []
    for elemento in re.findall(padrao_da_tag, pagina, re.I):
        achou = re.search(atributo + r'\s*=\s*([^\s>]+)', elemento, re.I)
        if achou:
            valores.append(_sem_aspas(achou.group(1)))
    return valores


def test_a_pagina_e_servida_como_html(cliente):
    resposta = cliente.get('/')
    assert resposta.status_code == 200
    assert 'text/html' in resposta.headers.get('content-type', '')


def test_as_abas_tem_os_rotulos_exatos_e_estao_nessa_ordem(tela_norm, norm):
    alunos = norm('ALUNOS')
    docentes = norm('DOCENTES')
    assert alunos in tela_norm
    assert docentes in tela_norm
    assert tela_norm.index(alunos) < tela_norm.index(docentes)


def test_a_aba_alunos_e_marcada_como_ativa_no_inicio(pagina, js):
    marcacao = (
        re.search(r'class\s*=\s*[^\s>]*(active|ativa|selected)', pagina, re.I)
        or re.search(r'aria-selected', pagina, re.I)
        or ('hidden' in pagina)
        or ('classList' in js)
    )
    assert marcacao


def test_cada_aba_tem_o_botao_de_enviar(pagina_norm, norm):
    assert pagina_norm.count(norm('Enviar solicitação')) >= 2


def test_os_tres_blocos_aparecem_nas_duas_abas(pagina_norm, norm):
    for titulo in TITULOS_BLOCOS:
        assert pagina_norm.count(norm(titulo)) >= 2, titulo


def test_os_rotulos_comuns_aparecem_nas_duas_abas(pagina_norm, norm):
    for rotulo in ROTULOS_COMUNS:
        assert pagina_norm.count(norm(rotulo)) >= 2, rotulo


def test_os_rotulos_exclusivos_da_aba_alunos_estao_presentes(pagina_norm, norm):
    for rotulo in ROTULOS_DE_ALUNOS:
        assert norm(rotulo) in pagina_norm, rotulo


def test_as_opcoes_das_selecoes_da_aba_alunos(pagina_norm, norm):
    for opcao in OPCOES:
        assert norm(opcao) in pagina_norm, opcao


def test_o_cabecalho_traz_o_logotipo_e_o_nome_da_instituicao(pagina_norm, norm):
    assert 'usplogo' in pagina_norm
    assert norm('Universidade de São Paulo') in pagina_norm


def test_o_logotipo_e_servido_como_imagem(cliente, pagina):
    fontes = _valores_de_atributo(pagina, r'<img\b[^>]*>', 'src')
    logos = [fonte for fonte in fontes if 'usp-logo' in fonte]
    assert logos, 'o cabeçalho deveria exibir o logotipo assets/usp-logo.png'
    caminho = logos[0].split('?')[0].split('#')[0]
    if not caminho.startswith('/'):
        caminho = '/' + caminho
    resposta = cliente.get(caminho)
    assert resposta.status_code == 200


def test_todo_campo_tem_placeholder(pagina):
    campos = re.findall(r'<(?:input|textarea)\b[^>]*>', pagina, re.I)
    assert len(campos) >= 20, 'a página deveria ter os campos dos dois formulários'
    sem_placeholder = [
        campo for campo in campos if not re.search(r'placeholder\s*=', campo, re.I)
    ]
    assert not sem_placeholder, f'{len(sem_placeholder)} campos sem placeholder'


def test_o_placeholder_e_um_exemplo_e_nao_a_repeticao_do_rotulo(pagina, norm):
    exemplos = _valores_de_atributo(
        pagina, r'<(?:input|textarea)\b[^>]*>', 'placeholder'
    )
    assert exemplos, 'os campos deveriam ter placeholder'
    proibidos = {norm(rotulo) for rotulo in ROTULOS_COMUNS + ROTULOS_DE_ALUNOS}
    for bruto in re.findall(r'<label\b[^>]*>(.*?)</label>', pagina, re.S | re.I):
        texto = re.sub(r'<[^>]+>', ' ', bruto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        if texto:
            proibidos.add(norm(texto))
    for exemplo in exemplos:
        assert exemplo, 'há campo com placeholder vazio'
        assert norm(exemplo) not in proibidos, f'placeholder repete o rótulo: {exemplo}'


def test_os_arquivos_estaticos_sao_servidos(css, js):
    assert css.strip()
    assert js.strip()


def test_as_cores_da_identidade_usp_estao_no_css(css):
    folha = css.lower()
    assert '#1094ab' in folha
    assert '#64c4d2' in folha
    assert '#fcb421' in folha


def test_a_fonte_e_open_sans_ou_outra_sem_serifa(css):
    assert 'open sans' in css.lower() or 'sans-serif' in css.lower()


def test_o_app_js_conversa_com_o_backend(js):
    assert 'fetch(' in js


def test_o_app_js_formata_os_campos_quando_o_usuario_sai_deles(js):
    assert any(evento in js for evento in ('blur', 'focusout', 'change'))
    assert 'R$' in js
