'use strict';

const F = (nome, rotulo, tipo, placeholder, largura, extra = {}) =>
  ({ nome, rotulo, tipo, placeholder, largura, ...extra });

const NIVEL_OPCOES = ['Mestrado', 'Doutorado'];
const TIPO_AUXILIO_OPCOES = ['Participação em evento', 'Banca de exame ou defesa', 'Outro'];
const APRESENTACAO_OPCOES = ['Pôster', 'Apresentação oral', 'Outra', 'Não irá apresentar trabalho'];

const SOLICITANTE_ALUNOS = [
  F('nome', 'NOME COMPLETO - SEM ABREVIAR', 'text', 'Maria de Souza Silva', 5),
  F('n_usp', 'N. USP', 'text', '1234567', 2),
  F('programa', 'PROGRAMA', 'text', 'Ciência da Computação', 5),
  F('nivel', 'NÍVEL', 'select', '', 2, { opcoes: NIVEL_OPCOES, textoVazio: 'Selecione o nível' }),
  F('tipo_auxilio', 'TIPO DE AUXÍLIO', 'select', '', 4, { opcoes: TIPO_AUXILIO_OPCOES, textoVazio: 'Selecione o tipo de auxílio' }),
  F('email', 'E-MAIL', 'text', 'maria.silva@usp.br', 6),
  F('nome_evento', 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', 'text', 'Congresso Brasileiro de Computação', 6),
  F('periodo_evento', 'PERÍODO DO EVENTO, EXAME OU DEFESA', 'text', '10/09/2025 a 14/09/2025', 3),
  F('cidade_evento', 'CIDADE DO EVENTO, EXAME OU DEFESA', 'text', 'Rio de Janeiro', 3),
  F('estado_evento', 'ESTADO DO EVENTO, EXAME OU DEFESA', 'text', 'RJ', 3),
  F('pais_evento', 'PAÍS DO EVENTO, EXAME OU DEFESA', 'text', 'Brasil', 3),
  F('link_evento', 'LINK DO EVENTO, EXAME OU DEFESA', 'text', 'https://www.example.org/congresso', 3, { opcional: true }),
  F('valor', 'VALOR SOLICITADO (R$)', 'text', '150000', 3),
  F('apresentacao', 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', 'select', '', 5, { opcoes: APRESENTACAO_OPCOES, textoVazio: 'Selecione uma opção' }),
  F('detalhamento', 'DETALHAMENTO DO PEDIDO', 'textarea', 'Ex.: inscrição no evento e passagem aérea de ida e volta', 7),
];

const SOLICITANTE_DOCENTES = [
  F('nome', 'NOME COMPLETO - SEM ABREVIAR', 'text', 'João Cardoso Ferraz', 5),
  F('n_usp', 'N. USP', 'text', '7654321', 2),
  F('programa', 'PROGRAMA', 'text', 'Estatística', 5),
  F('email', 'E-MAIL', 'text', 'joao.ferraz@usp.br', 6),
  F('nome_evento', 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', 'text', 'Banca de defesa de doutorado de Ana Chen', 6),
  F('periodo_evento', 'PERÍODO DO EVENTO, EXAME OU DEFESA', 'text', '10/09/2025 a 14/09/2025', 3),
  F('cidade_evento', 'CIDADE DO EVENTO, EXAME OU DEFESA', 'text', 'São Paulo', 3),
  F('estado_evento', 'ESTADO DO EVENTO, EXAME OU DEFESA', 'text', 'SP', 3),
  F('pais_evento', 'PAÍS DO EVENTO, EXAME OU DEFESA', 'text', 'Brasil', 3),
  F('link_evento', 'LINK DO EVENTO, EXAME OU DEFESA', 'text', 'https://www.ime.usp.br', 4, { opcional: true }),
  F('valor', 'VALOR SOLICITADO (R$)', 'text', '150000', 4),
  F('apresentacao', 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', 'select', '', 4, { opcoes: APRESENTACAO_OPCOES, textoVazio: 'Selecione uma opção' }),
  F('detalhamento', 'DETALHAMENTO DO PEDIDO', 'textarea', 'Ex.: diária de hotel para participação na banca', 12),
];

const CAMPOS_ENDERECO = [
  F('data_nascimento', 'DATA DE NASCIMENTO', 'text', '01011980', 3),
  F('logradouro', 'LOGRADOURO', 'text', 'Rua do Anfiteatro', 4),
  F('numero', 'NÚMERO', 'text', '101', 2),
  F('complemento', 'COMPLEMENTO', 'text', 'Sala 208', 3, { opcional: true }),
  F('bairro', 'BAIRRO', 'text', 'Butantã', 3),
  F('cep', 'CEP', 'text', '05508090', 3),
  F('cidade', 'CIDADE', 'text', 'São Paulo', 3),
  F('estado', 'ESTADO', 'text', 'SP', 3),
];

const CAMPOS_PAGAMENTO = [
  F('cpf', 'CPF (SEPARADOS POR PONTOS E TRAÇO)', 'text', '12345678909', 3),
  F('rg_rnm', 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', 'text', '12.345.678-9', 3),
  F('nome_banco', 'NOME DO BANCO', 'text', 'Banco do Brasil', 2),
  F('agencia', 'NÚMERO DA AGÊNCIA', 'text', '1234', 2),
  F('conta', 'NÚMERO DA CONTA', 'text', '12345-6', 2),
];

const BLOCOS = {
  alunos: [
    { titulo: 'SOLICITANTE E EVENTO', campos: SOLICITANTE_ALUNOS },
    { titulo: 'ENDEREÇO DO SOLICITANTE', campos: CAMPOS_ENDERECO },
    { titulo: 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO', campos: CAMPOS_PAGAMENTO },
  ],
  docentes: [
    { titulo: 'SOLICITANTE E EVENTO', campos: SOLICITANTE_DOCENTES },
    { titulo: 'ENDEREÇO DO SOLICITANTE', campos: CAMPOS_ENDERECO },
    { titulo: 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO', campos: CAMPOS_PAGAMENTO },
  ],
};

const FORMATADORES = {
  valor(campo) {
    const digitos = campo.value.replace(/\D/g, '');
    if (!digitos) {
      campo.value = '';
      return;
    }
    const numero = digitos.replace(/^0+/, '') || '0';
    const centavos = numero.length > 2 ? numero.slice(-2) : numero.padStart(2, '0');
    const reais = numero.length > 2 ? numero.slice(0, -2) : '0';
    campo.value = 'R$ ' + reais.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + centavos;
  },
  cpf(campo) {
    let v = campo.value.replace(/\D/g, '').slice(0, 11);
    if (v.length >= 4) v = v.slice(0, 3) + '.' + v.slice(3);
    if (v.length >= 8) v = v.slice(0, 7) + '.' + v.slice(7);
    if (v.length >= 12) v = v.slice(0, 11) + '-' + v.slice(11);
    campo.value = v;
  },
  cep(campo) {
    let v = campo.value.replace(/\D/g, '').slice(0, 8);
    if (v.length >= 6) v = v.slice(0, 5) + '-' + v.slice(5);
    campo.value = v;
  },
  data_nascimento(campo) {
    let v = campo.value.replace(/\D/g, '').slice(0, 8);
    if (v.length >= 3) v = v.slice(0, 2) + '/' + v.slice(2);
    if (v.length >= 6) v = v.slice(0, 5) + '/' + v.slice(5);
    campo.value = v;
  },
};

function criarCampo(campo, tipoAba) {
  const div = document.createElement('div');
  div.className = 'campo';
  div.style.gridColumn = 'span ' + campo.largura;

  const rotulo = document.createElement('label');
  rotulo.htmlFor = tipoAba + '-' + campo.nome;
  rotulo.textContent = campo.rotulo;
  div.appendChild(rotulo);

  let controle;
  if (campo.tipo === 'select') {
    controle = document.createElement('select');
    const vazio = document.createElement('option');
    vazio.value = '';
    vazio.textContent = campo.textoVazio;
    controle.appendChild(vazio);
    campo.opcoes.forEach(opcao => {
      const item = document.createElement('option');
      item.value = opcao;
      item.textContent = opcao;
      controle.appendChild(item);
    });
  } else if (campo.tipo === 'textarea') {
    controle = document.createElement('textarea');
    controle.rows = 2;
  } else {
    controle = document.createElement('input');
    controle.type = 'text';
  }
  controle.id = tipoAba + '-' + campo.nome;
  controle.name = campo.nome;
  if (campo.placeholder) {
    controle.placeholder = campo.placeholder;
  }
  if (FORMATADORES[campo.nome]) {
    controle.addEventListener('blur', () => FORMATADORES[campo.nome](controle));
  }
  div.appendChild(controle);
  return div;
}

function montarFormulario(tipoAba) {
  const form = document.getElementById('form-' + tipoAba);
  const aviso = document.createElement('div');
  aviso.className = 'erros';
  aviso.hidden = true;
  form.appendChild(aviso);

  BLOCOS[tipoAba].forEach(bloco => {
    const secao = document.createElement('section');
    secao.className = 'bloco';
    const titulo = document.createElement('h2');
    titulo.textContent = bloco.titulo;
    secao.appendChild(titulo);
    const grade = document.createElement('div');
    grade.className = 'grade';
    bloco.campos.forEach(campo => grade.appendChild(criarCampo(campo, tipoAba)));
    secao.appendChild(grade);
    form.appendChild(secao);
  });

  const botao = document.createElement('button');
  botao.type = 'submit';
  botao.textContent = 'Enviar solicitação';
  form.appendChild(botao);

  form.addEventListener('submit', evento => {
    evento.preventDefault();
    enviar(tipoAba, form);
  });
}

function coletarDados(form) {
  const dados = {};
  form.querySelectorAll('[name]').forEach(controle => {
    dados[controle.name] = controle.value.trim();
  });
  return dados;
}

async function enviar(tipoAba, form) {
  const aviso = form.querySelector('.erros');
  const resposta = await fetch('/api/solicitar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/' },
    body: JSON.stringify({ tipo: tipoAba, dados: coletarDados(form) }),
  });
  const resultado = await resposta.();
  if (resultado.oficio) {
    document.getElementById('area-formulario').hidden = true;
    document.getElementById('oficio').textContent = resultado.oficio;
    document.getElementById('confirmacao').hidden = false;
    return;
  }
  aviso.replaceChildren(...resultado.erros.map(mensagem => {
    const paragrafo = document.createElement('p');
    paragrafo.textContent = mensagem;
    return paragrafo;
  }));
  aviso.hidden = false;
}

function ligarAbas() {
  const abas = Array.from(document.querySelectorAll('.aba'));
  abas.forEach(aba => aba.addEventListener('click', () => {
    abas.forEach(outra => {
      const ativa = outra === aba;
      outra.classList.toggle('ativa', ativa);
      outra.setAttribute('aria-selected', String(ativa));
    });
    document.querySelectorAll('.formulario').forEach(form => {
      form.hidden = form.id !== 'form-' + aba.dataset.aba;
    });
  }));
}

ligarAbas();
montarFormulario('alunos');
montarFormulario('docentes');
