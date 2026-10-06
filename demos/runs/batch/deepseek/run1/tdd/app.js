const CAMPOS_ENDERECO = [
  { nome: 'data_nascimento', rotulo: 'DATA DE NASCIMENTO', placeholder: '01/02/1980', formato: 'data' },
  { nome: 'logradouro', rotulo: 'LOGRADOURO', placeholder: 'Rua das Flores', largo: 2 },
  { nome: 'numero', rotulo: 'NÚMERO', placeholder: '100' },
  { nome: 'complemento', rotulo: 'COMPLEMENTO', placeholder: 'Apto 1' },
  { nome: 'bairro', rotulo: 'BAIRRO', placeholder: 'Centro' },
  { nome: 'cep', rotulo: 'CEP', placeholder: '05508-090', formato: 'cep' },
  { nome: 'cidade', rotulo: 'CIDADE', placeholder: 'São Paulo' },
  { nome: 'estado', rotulo: 'ESTADO', placeholder: 'SP' },
];

const CAMPOS_PAGAMENTO = [
  { nome: 'cpf', rotulo: 'CPF (SEPARADOS POR PONTOS E TRAÇO)', placeholder: '111.444.777-35', formato: 'cpf' },
  { nome: 'rg', rotulo: 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', placeholder: '12.345.678-9' },
  { nome: 'banco', rotulo: 'NOME DO BANCO', placeholder: 'Banco do Brasil' },
  { nome: 'agencia', rotulo: 'NÚMERO DA AGÊNCIA', placeholder: '1234' },
  { nome: 'conta', rotulo: 'NÚMERO DA CONTA', placeholder: '12345-6' },
];

function camposSolicitante(aba) {
  const campos = [
    { nome: 'nome_completo', rotulo: 'NOME COMPLETO - SEM ABREVIAR', placeholder: 'Maria Silva', largo: 2 },
    { nome: 'n_usp', rotulo: 'N. USP', placeholder: '12345678' },
    { nome: 'programa', rotulo: 'PROGRAMA', placeholder: 'Ciência da Computação' },
  ];
  if (aba === 'alunos') {
    campos.push(
      { nome: 'nivel', rotulo: 'NÍVEL', opcoes: ['Mestrado', 'Doutorado'] },
      { nome: 'tipo_auxilio', rotulo: 'TIPO DE AUXÍLIO', opcoes: ['Participação em evento', 'Banca de exame ou defesa', 'Outro'] }
    );
  }
  campos.push(
    { nome: 'email', rotulo: 'E-MAIL', tipo: 'email', placeholder: 'maria@ime.usp.br' },
    { nome: 'nome_evento', rotulo: 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', placeholder: 'Congresso Brasileiro', largo: 2 },
    { nome: 'periodo', rotulo: 'PERÍODO DO EVENTO, EXAME OU DEFESA', placeholder: '01/01/2025 a 05/01/2025' },
    { nome: 'cidade_evento', rotulo: 'CIDADE DO EVENTO, EXAME OU DEFESA', placeholder: 'São Paulo' },
    { nome: 'estado_evento', rotulo: 'ESTADO DO EVENTO, EXAME OU DEFESA', placeholder: 'SP' },
    { nome: 'pais_evento', rotulo: 'PAÍS DO EVENTO, EXAME OU DEFESA', placeholder: 'Brasil' },
    { nome: 'link_evento', rotulo: 'LINK DO EVENTO, EXAME OU DEFESA', placeholder: 'http://exemplo.com', largo: 2 },
    { nome: 'valor_solicitado', rotulo: 'VALOR SOLICITADO (R$)', placeholder: 'R$ 1.500,00', formato: 'valor' },
    { nome: 'detalhamento', rotulo: 'DETALHAMENTO DO PEDIDO', placeholder: 'Passagem e hospedagem', area: true, largo: 3 },
    { nome: 'apresentacao', rotulo: 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', opcoes: ['Pôster', 'Apresentação oral', 'Outra', 'Não irá apresentar trabalho'] }
  );
  return campos;
}

function formatarValor(valor) {
  const digitos = valor.replace(/\D/g, '');
  if (!digitos) return '';
  return 'R$ ' + (parseInt(digitos, 10) / 100).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatarCPF(valor) {
  return valor
    .replace(/\D/g, '')
    .slice(0, 11)
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
}

function formatarCEP(valor) {
  return valor
    .replace(/\D/g, '')
    .slice(0, 8)
    .replace(/(\d{5})(\d{1,3})/, '$1-$2');
}

function formatarData(valor) {
  return valor
    .replace(/\D/g, '')
    .slice(0, 8)
    .replace(/(\d{2})(\d{2})(\d{1,4})/, '$1/$2/$3');
}

const FORMATADORES = {
  valor: formatarValor,
  cpf: formatarCPF,
  cep: formatarCEP,
  data: formatarData,
};

function criarCampo(def, aba) {
  const wrapper = document.createElement('div');
  wrapper.className = 'campo';
  wrapper.style.gridColumn = 'span ' + (def.largo || 1);

  const id = aba + '_' + def.nome;
  const label = document.createElement('label');
  label.textContent = def.rotulo;
  label.setAttribute('for', id);
  wrapper.appendChild(label);

  let input;
  if (def.opcoes) {
    input = document.createElement('select');
    const vazio = document.createElement('option');
    vazio.value = '';
    vazio.textContent = 'Selecione';
    input.appendChild(vazio);
    def.opcoes.forEach(function (opcao) {
      const o = document.createElement('option');
      o.value = opcao;
      o.textContent = opcao;
      input.appendChild(o);
    });
  } else if (def.area) {
    input = document.createElement('textarea');
    input.rows = 2;
  } else {
    input = document.createElement('input');
    input.type = def.tipo || 'text';
  }

  input.id = id;
  input.name = def.nome;
  if (def.placeholder && !def.opcoes) {
    input.placeholder = def.placeholder;
  }
  if (def.formato) {
    input.dataset.formato = def.formato;
  }
  wrapper.appendChild(input);
  return wrapper;
}

function construirFormulario(aba) {
  const form = document.createElement('form');
  form.className = 'formulario';
  form.noValidate = true;

  const abaInput = document.createElement('input');
  abaInput.type = 'hidden';
  abaInput.name = 'aba';
  abaInput.value = aba;
  form.appendChild(abaInput);

  const erros = document.createElement('div');
  erros.className = 'erros escondido';
  form.appendChild(erros);

  const blocos = [
    { titulo: 'SOLICITANTE E EVENTO', campos: camposSolicitante(aba) },
    { titulo: 'ENDEREÇO DO SOLICITANTE', campos: CAMPOS_ENDERECO },
    { titulo: 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO', campos: CAMPOS_PAGAMENTO },
  ];

  blocos.forEach(function (bloco) {
    const fieldset = document.createElement('fieldset');
    const legend = document.createElement('legend');
    legend.textContent = bloco.titulo;
    fieldset.appendChild(legend);
    const grade = document.createElement('div');
    grade.className = 'grade';
    bloco.campos.forEach(function (def) {
      grade.appendChild(criarCampo(def, aba));
    });
    fieldset.appendChild(grade);
    form.appendChild(fieldset);
  });

  const botao = document.createElement('button');
  botao.type = 'submit';
  botao.className = 'enviar';
  botao.textContent = 'Enviar solicitação';
  form.appendChild(botao);

  form.addEventListener('submit', enviar);
  return form;
}

async function enviar(evento) {
  evento.preventDefault();
  const form = evento.target;
  const resposta = await fetch('/solicitar', {
    method: 'POST',
    body: new FormData(form),
  });
  const dados = await resposta.json();
  const caixa = form.querySelector('.erros');

  if (dados.erros && dados.erros.length) {
    caixa.innerHTML = '';
    dados.erros.forEach(function (msg) {
      const p = document.createElement('p');
      p.textContent = msg;
      caixa.appendChild(p);
    });
    caixa.classList.remove('escondido');
    return;
  }

  caixa.classList.add('escondido');
  document.getElementById('oficio').textContent = dados.oficio;
  document.getElementById('abas').classList.add('escondido');
  document.querySelectorAll('.painel').forEach(function (painel) {
    painel.classList.add('escondido');
  });
  document.getElementById('confirmacao').classList.remove('escondido');
}

function selecionarAba(aba) {
  document.querySelectorAll('.aba').forEach(function (botao) {
    const ativa = botao.dataset.aba === aba;
    botao.classList.toggle('ativa', ativa);
    botao.setAttribute('aria-selected', ativa ? 'true' : 'false');
  });
  document.getElementById('form-alunos').classList.toggle('escondido', aba !== 'alunos');
  document.getElementById('form-docentes').classList.toggle('escondido', aba !== 'docentes');
}

document.querySelectorAll('.aba').forEach(function (botao) {
  botao.addEventListener('click', function () {
    selecionarAba(botao.dataset.aba);
  });
});

document.addEventListener(
  'blur',
  function (evento) {
    const alvo = evento.target;
    const formato = alvo.dataset && alvo.dataset.formato;
    if (formato && FORMATADORES[formato]) {
      alvo.value = FORMATADORES[formato](alvo.value);
    }
  },
  true
);

document.getElementById('form-alunos').appendChild(construirFormulario('alunos'));
document.getElementById('form-docentes').appendChild(construirFormulario('docentes'));
