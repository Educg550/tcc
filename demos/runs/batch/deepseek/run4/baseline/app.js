const BLOCOS = [
  {
    titulo: 'SOLICITANTE E EVENTO',
    campos: [
      { name: 'nome_completo', rotulo: 'NOME COMPLETO - SEM ABREVIAR', tipo: 'texto', ph: 'Maria da Silva Santos', span: 6 },
      { name: 'n_usp', rotulo: 'N. USP', tipo: 'digitos', ph: '12345678', span: 3 },
      { name: 'programa', rotulo: 'PROGRAMA', tipo: 'texto', ph: 'Ciência da Computação', span: 3 },
      { name: 'email', rotulo: 'E-MAIL', tipo: 'email', ph: 'maria.silva@usp.br', span: 6 },
      { name: 'nivel', rotulo: 'NÍVEL', tipo: 'select', opcoes: ['Mestrado', 'Doutorado'], somenteAlunos: true, span: 3 },
      { name: 'tipo_auxilio', rotulo: 'TIPO DE AUXÍLIO', tipo: 'select', opcoes: ['Participação em evento', 'Banca de exame ou defesa', 'Outro'], somenteAlunos: true, span: 3 },
      { name: 'nome_evento', rotulo: 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', tipo: 'texto', ph: 'Simpósio Brasileiro de Computação', span: 6 },
      { name: 'periodo', rotulo: 'PERÍODO DO EVENTO, EXAME OU DEFESA', tipo: 'texto', ph: '10 a 15 de julho de 2025', span: 6 },
      { name: 'cidade_evento', rotulo: 'CIDADE DO EVENTO, EXAME OU DEFESA', tipo: 'texto', ph: 'São Paulo', span: 3 },
      { name: 'estado_evento', rotulo: 'ESTADO DO EVENTO, EXAME OU DEFESA', tipo: 'texto', ph: 'SP', span: 2 },
      { name: 'pais_evento', rotulo: 'PAÍS DO EVENTO, EXAME OU DEFESA', tipo: 'texto', ph: 'Brasil', span: 3 },
      { name: 'link_evento', rotulo: 'LINK DO EVENTO, EXAME OU DEFESA', tipo: 'texto', ph: 'https://evento.exemplo.br', span: 4 },
      { name: 'valor', rotulo: 'VALOR SOLICITADO (R$)', tipo: 'moeda', ph: 'R$ 1.500,00', span: 4 },
      { name: 'apresentacao', rotulo: 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', tipo: 'select', opcoes: ['Pôster', 'Apresentação oral', 'Outra', 'Não irá apresentar trabalho'], span: 8 },
      { name: 'detalhamento', rotulo: 'DETALHAMENTO DO PEDIDO', tipo: 'textarea', ph: 'Descreva as despesas previstas: passagem, hospedagem, inscrição...', span: 12 },
    ],
  },
  {
    titulo: 'ENDEREÇO DO SOLICITANTE',
    campos: [
      { name: 'data_nascimento', rotulo: 'DATA DE NASCIMENTO', tipo: 'data', ph: '01/02/1980', span: 3 },
      { name: 'logradouro', rotulo: 'LOGRADOURO', tipo: 'texto', ph: 'Rua do Matão', span: 6 },
      { name: 'numero', rotulo: 'NÚMERO', tipo: 'texto', ph: '1010', span: 3 },
      { name: 'complemento', rotulo: 'COMPLEMENTO', tipo: 'texto', ph: 'Bloco B, apto 42', span: 4 },
      { name: 'bairro', rotulo: 'BAIRRO', tipo: 'texto', ph: 'Butantã', span: 4 },
      { name: 'cep', rotulo: 'CEP', tipo: 'cep', ph: '05508-090', span: 4 },
      { name: 'cidade', rotulo: 'CIDADE', tipo: 'texto', ph: 'São Paulo', span: 8 },
      { name: 'estado', rotulo: 'ESTADO', tipo: 'texto', ph: 'SP', span: 4 },
    ],
  },
  {
    titulo: 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
    campos: [
      { name: 'cpf', rotulo: 'CPF (SEPARADOS POR PONTOS E TRAÇO)', tipo: 'cpf', ph: '123.456.789-09', span: 4 },
      { name: 'rg', rotulo: 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', tipo: 'texto', ph: '12.345.678-9', span: 4 },
      { name: 'banco', rotulo: 'NOME DO BANCO', tipo: 'texto', ph: 'Banco do Brasil', span: 4 },
      { name: 'agencia', rotulo: 'NÚMERO DA AGÊNCIA', tipo: 'digitos', ph: '1234', span: 4 },
      { name: 'conta', rotulo: 'NÚMERO DA CONTA', tipo: 'texto', ph: '12345-6', span: 4 },
    ],
  },
];

function formatarMoeda(valor) {
  let digitos = valor.replace(/\D/g, '').replace(/^0+(?=\d)/, '');
  if (!digitos) return '';
  digitos = digitos.padStart(3, '0');
  const centavos = digitos.slice(-2);
  const inteiro = digitos.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `R$ ${inteiro},${centavos}`;
}

function formatarCPF(valor) {
  const d = valor.replace(/\D/g, '').slice(0, 11);
  if (d.length > 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
  if (d.length > 6) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  if (d.length > 3) return `${d.slice(0, 3)}.${d.slice(3)}`;
  return d;
}

function formatarCEP(valor) {
  const d = valor.replace(/\D/g, '').slice(0, 8);
  if (d.length <= 5) return d;
  return `${d.slice(0, 5)}-${d.slice(5)}`;
}

function formatarData(valor) {
  const d = valor.replace(/\D/g, '').slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return `${d.slice(0, 2)}/${d.slice(2)}`;
  return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
}

const FORMATADORES = {
  moeda: formatarMoeda,
  cpf: formatarCPF,
  cep: formatarCEP,
  data: formatarData,
};

function criarCampo(campo, aba) {
  const div = document.createElement('div');
  div.className = 'campo';
  div.style.gridColumn = `span ${campo.span}`;
  const id = `${aba}-${campo.name}`;

  const label = document.createElement('label');
  label.textContent = campo.rotulo;
  label.htmlFor = id;

  let el;
  if (campo.tipo === 'select') {
    el = document.createElement('select');
    const vazio = document.createElement('option');
    vazio.value = '';
    vazio.textContent = 'Selecione';
    el.appendChild(vazio);
    campo.opcoes.forEach(opcao => {
      const item = document.createElement('option');
      item.value = opcao;
      item.textContent = opcao;
      el.appendChild(item);
    });
  } else if (campo.tipo === 'textarea') {
    el = document.createElement('textarea');
    el.rows = 2;
    el.placeholder = campo.ph;
  } else {
    el = document.createElement('input');
    el.type = 'text';
    el.placeholder = campo.ph;
    if (campo.tipo === 'digitos') el.inputMode = 'numeric';
    if (campo.tipo === 'email') el.inputMode = 'email';
  }
  el.id = id;
  el.name = campo.name;

  if (FORMATADORES[campo.tipo]) {
    el.addEventListener('blur', () => {
      el.value = FORMATADORES[campo.tipo](el.value);
    });
  }

  div.appendChild(label);
  div.appendChild(el);
  return div;
}

function renderForm(form, aba) {
  const errosBox = document.createElement('div');
  errosBox.className = 'erros';
  errosBox.hidden = true;
  form.appendChild(errosBox);

  BLOCOS.forEach(bloco => {
    const secao = document.createElement('section');
    secao.className = 'bloco';

    const titulo = document.createElement('h2');
    titulo.textContent = bloco.titulo;
    secao.appendChild(titulo);

    const grade = document.createElement('div');
    grade.className = 'grade';
    bloco.campos
      .filter(campo => aba === 'alunos' || !campo.somenteAlunos)
      .forEach(campo => grade.appendChild(criarCampo(campo, aba)));
    secao.appendChild(grade);
    form.appendChild(secao);
  });

  const botao = document.createElement('button');
  botao.type = 'submit';
  botao.className = 'enviar';
  botao.textContent = 'Enviar solicitação';
  form.appendChild(botao);

  form.addEventListener('submit', evento => {
    evento.preventDefault();
    enviar(form, aba);
  });
}

async function enviar(form, aba) {
  const errosBox = form.querySelector('.erros');
  const dados = { aba };
  form.querySelectorAll('[name]').forEach(el => {
    dados[el.name] = el.value;
  });

  const resposta = await fetch('/api/solicitacao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
  });
  const resultado = await resposta.json();

  if (resultado.erros && resultado.erros.length) {
    errosBox.innerHTML = '';
    resultado.erros.forEach(mensagem => {
      const linha = document.createElement('div');
      linha.textContent = mensagem;
      errosBox.appendChild(linha);
    });
    errosBox.hidden = false;
    return;
  }

  errosBox.hidden = true;
  document.getElementById('formularios').hidden = true;
  document.getElementById('confirmacao').hidden = false;
  document.getElementById('oficio').textContent = resultado.oficio;
}

document.querySelectorAll('.aba').forEach(botao => {
  botao.addEventListener('click', () => {
    const aba = botao.dataset.aba;
    document.querySelectorAll('.aba').forEach(b => {
      b.classList.toggle('ativa', b === botao);
    });
    document.getElementById('form-alunos').hidden = aba !== 'alunos';
    document.getElementById('form-docentes').hidden = aba !== 'docentes';
  });
});

renderForm(document.getElementById('form-alunos'), 'alunos');
renderForm(document.getElementById('form-docentes'), 'docentes');
