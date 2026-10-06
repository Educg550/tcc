const FORMATADORES = {
  valor(v) {
    const d = v.replace(/\D/g, '');
    if (!d) return '';
    const centavos = parseInt(d, 10);
    const inteiro = Math.floor(centavos / 100);
    const resto = String(centavos % 100).padStart(2, '0');
    return 'R$ ' + inteiro.toLocaleString('pt-BR') + ',' + resto;
  },
  cpf(v) {
    const d = v.replace(/\D/g, '').slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + '.' + d.slice(3);
    return d;
  },
  cep(v) {
    const d = v.replace(/\D/g, '').slice(0, 8);
    if (d.length > 5) return d.slice(0, 5) + '-' + d.slice(5);
    return d;
  },
  data(v) {
    const d = v.replace(/\D/g, '').slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + '/' + d.slice(2);
    return d;
  },
};

function camposEvento(tipo) {
  const c = [
    { n: 'nome', r: 'NOME COMPLETO - SEM ABREVIAR', p: 'Maria da Silva Santos', s: 4 },
    { n: 'n_usp', r: 'N. USP', p: '12345678', s: 2 },
  ];
  if (tipo === 'alunos') {
    c.push({ n: 'programa', r: 'PROGRAMA', p: 'Ci\u00eancia da Computa\u00e7\u00e3o', s: 2 });
    c.push({ n: 'nivel', r: 'N\u00cdVEL', p: 'Mestrado', s: 2, sel: ['Mestrado', 'Doutorado'] });
    c.push({ n: 'tipo_auxilio', r: 'TIPO DE AUX\u00cdLIO', p: 'Participa\u00e7\u00e3o em evento', s: 2, sel: ['Participa\u00e7\u00e3o em evento', 'Banca de exame ou defesa', 'Outro'] });
    c.push({ n: 'email', r: 'E-MAIL', p: 'maria@usp.br', s: 4 });
    c.push({ n: 'evento', r: 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', p: 'Congresso Brasileiro de Computa\u00e7\u00e3o', s: 4 });
    c.push({ n: 'periodo', r: 'PER\u00cdODO DO EVENTO, EXAME OU DEFESA', p: '10 a 15 de julho de 2024', s: 4 });
    c.push({ n: 'cidade_evento', r: 'CIDADE DO EVENTO, EXAME OU DEFESA', p: 'S\u00e3o Paulo', s: 2 });
    c.push({ n: 'estado_evento', r: 'ESTADO DO EVENTO, EXAME OU DEFESA', p: 'SP', s: 2 });
    c.push({ n: 'pais_evento', r: 'PA\u00cdS DO EVENTO, EXAME OU DEFESA', p: 'Brasil', s: 2 });
    c.push({ n: 'link_evento', r: 'LINK DO EVENTO, EXAME OU DEFESA', p: 'https://evento.usp.br', s: 3 });
    c.push({ n: 'valor', r: 'VALOR SOLICITADO (R$)', p: 'R$ 1.500,00', s: 3, fmt: 'valor' });
    c.push({ n: 'apresentacao', r: 'IR\u00c1 APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', p: 'Apresenta\u00e7\u00e3o oral', s: 4, sel: ['P\u00f4ster', 'Apresenta\u00e7\u00e3o oral', 'Outra', 'N\u00e3o ir\u00e1 apresentar trabalho'] });
    c.push({ n: 'detalhamento', r: 'DETALHAMENTO DO PEDIDO', p: 'Passagens, hospedagem e taxa de inscri\u00e7\u00e3o', s: 8, area: true });
  } else {
    c.push({ n: 'programa', r: 'PROGRAMA', p: 'Ci\u00eancia da Computa\u00e7\u00e3o', s: 3 });
    c.push({ n: 'email', r: 'E-MAIL', p: 'maria@usp.br', s: 3 });
    c.push({ n: 'evento', r: 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', p: 'Congresso Brasileiro de Computa\u00e7\u00e3o', s: 4 });
    c.push({ n: 'periodo', r: 'PER\u00cdODO DO EVENTO, EXAME OU DEFESA', p: '10 a 15 de julho de 2024', s: 4 });
    c.push({ n: 'apresentacao', r: 'IR\u00c1 APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', p: 'Apresenta\u00e7\u00e3o oral', s: 4, sel: ['P\u00f4ster', 'Apresenta\u00e7\u00e3o oral', 'Outra', 'N\u00e3o ir\u00e1 apresentar trabalho'] });
    c.push({ n: 'cidade_evento', r: 'CIDADE DO EVENTO, EXAME OU DEFESA', p: 'S\u00e3o Paulo', s: 2 });
    c.push({ n: 'estado_evento', r: 'ESTADO DO EVENTO, EXAME OU DEFESA', p: 'SP', s: 2 });
    c.push({ n: 'pais_evento', r: 'PA\u00cdS DO EVENTO, EXAME OU DEFESA', p: 'Brasil', s: 2 });
    c.push({ n: 'link_evento', r: 'LINK DO EVENTO, EXAME OU DEFESA', p: 'https://evento.usp.br', s: 3 });
    c.push({ n: 'valor', r: 'VALOR SOLICITADO (R$)', p: 'R$ 1.500,00', s: 3, fmt: 'valor' });
    c.push({ n: 'detalhamento', r: 'DETALHAMENTO DO PEDIDO', p: 'Passagens, hospedagem e taxa de inscri\u00e7\u00e3o', s: 12, area: true });
  }
  return c;
}

function camposEndereco() {
  return [
    { n: 'data_nascimento', r: 'DATA DE NASCIMENTO', p: '01/02/1980', s: 2, fmt: 'data' },
    { n: 'logradouro', r: 'LOGRADOURO', p: 'Av. Prof. Luciano Gualberto', s: 4 },
    { n: 'numero', r: 'N\u00daMERO', p: '158', s: 2 },
    { n: 'complemento', r: 'COMPLEMENTO', p: 'Sala 100', s: 2 },
    { n: 'bairro', r: 'BAIRRO', p: 'Butant\u00e3', s: 2 },
    { n: 'cep', r: 'CEP', p: '05508-090', s: 2, fmt: 'cep' },
    { n: 'cidade', r: 'CIDADE', p: 'S\u00e3o Paulo', s: 5 },
    { n: 'estado', r: 'ESTADO', p: 'SP', s: 5 },
  ];
}

function camposPagamento() {
  return [
    { n: 'cpf', r: 'CPF (SEPARADOS POR PONTOS E TRA\u00c7O)', p: '123.456.789-09', s: 3, fmt: 'cpf' },
    { n: 'rg', r: 'RG / RNM (SEPARADOS POR PONTOS E TRA\u00c7O)', p: '12.345.678-9', s: 3 },
    { n: 'banco', r: 'NOME DO BANCO', p: 'Banco do Brasil', s: 2 },
    { n: 'agencia', r: 'N\u00daMERO DA AG\u00caNCIA', p: '1234', s: 2 },
    { n: 'conta', r: 'N\u00daMERO DA CONTA', p: '12345-6', s: 2 },
  ];
}

function montarCampo(c) {
  const label = document.createElement('label');
  label.className = 'campo';
  label.style.gridColumn = 'span ' + c.s;

  const rotulo = document.createElement('span');
  rotulo.className = 'rotulo';
  rotulo.textContent = c.r;
  rotulo.title = c.r;
  label.appendChild(rotulo);

  let el;
  if (c.sel) {
    el = document.createElement('select');
    const ph = document.createElement('option');
    ph.value = '';
    ph.textContent = 'Ex.: ' + c.p;
    el.appendChild(ph);
    c.sel.forEach(o => {
      const op = document.createElement('option');
      op.value = o;
      op.textContent = o;
      el.appendChild(op);
    });
  } else if (c.area) {
    el = document.createElement('textarea');
    el.rows = 2;
    el.placeholder = c.p;
  } else {
    el = document.createElement('input');
    el.type = 'text';
    el.placeholder = c.p;
  }
  el.name = c.n;
  if (c.fmt) {
    el.addEventListener('blur', () => {
      el.value = FORMATADORES[c.fmt](el.value);
    });
  }
  label.appendChild(el);
  return label;
}

const BLOCOS = tipo => [
  { titulo: 'SOLICITANTE E EVENTO', campos: camposEvento(tipo) },
  { titulo: 'ENDERE\u00c7O DO SOLICITANTE', campos: camposEndereco() },
  { titulo: 'INFORMA\u00c7\u00d5ES PARA PAGAMENTO / REEMBOLSO', campos: camposPagamento() },
];

function montarFormulario(tipo) {
  const form = document.createElement('form');
  form.className = 'formulario';
  form.dataset.tipo = tipo;
  form.noValidate = true;

  const erros = document.createElement('div');
  erros.className = 'erros';
  form.appendChild(erros);

  BLOCOS(tipo).forEach(b => {
    const sec = document.createElement('section');
    sec.className = 'bloco';
    const h = document.createElement('h3');
    h.textContent = b.titulo;
    sec.appendChild(h);
    const grade = document.createElement('div');
    grade.className = 'grade';
    b.campos.forEach(c => grade.appendChild(montarCampo(c)));
    sec.appendChild(grade);
    form.appendChild(sec);
  });

  const botao = document.createElement('button');
  botao.type = 'submit';
  botao.className = 'botao-enviar';
  botao.textContent = 'Enviar solicita\u00e7\u00e3o';
  form.appendChild(botao);

  form.addEventListener('submit', ev => {
    ev.preventDefault();
    enviar(form);
  });
  return form;
}

async function enviar(form) {
  const dados = { tipo: form.dataset.tipo };
  form.querySelectorAll('input, select, textarea').forEach(el => {
    dados[el.name] = el.value;
  });

  const resp = await fetch('/api/solicitar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
  });
  const json = await resp.json();

  const erros = form.querySelector('.erros');
  if (json.erros) {
    erros.textContent = json.erros.join('\n');
    erros.classList.add('visivel');
    return;
  }

  erros.classList.remove('visivel');
  document.getElementById('conteudo').classList.add('oculto');
  document.querySelector('.abas').classList.add('oculto');
  document.getElementById('oficio').textContent = json.oficio;
  document.getElementById('confirmacao').classList.remove('oculto');
}

const formularios = {};

function ativar(tipo) {
  document.querySelectorAll('.aba').forEach(a => {
    a.classList.toggle('ativa', a.dataset.aba === tipo);
  });
  Object.entries(formularios).forEach(([t, f]) => {
    f.classList.toggle('oculto', t !== tipo);
  });
}

['alunos', 'docentes'].forEach(tipo => {
  const f = montarFormulario(tipo);
  if (tipo !== 'alunos') f.classList.add('oculto');
  document.getElementById('conteudo').appendChild(f);
  formularios[tipo] = f;
});

document.querySelectorAll('.aba').forEach(a => {
  a.addEventListener('click', () => ativar(a.dataset.aba));
});
