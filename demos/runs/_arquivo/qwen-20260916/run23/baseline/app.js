const cabecalho = document.querySelector('header');
const confirmacao = document.getElementById('confirmacao');
const oficioEl = document.getElementById('oficio');
const abas = document.querySelectorAll('.aba');
const paineis = document.querySelectorAll('.painel');

const BLOCOS = [
  {
    titulo: 'SOLICITANTE E EVENTO',
    campos: [
      { id: 'nome', rotulo: 'NOME COMPLETO - SEM ABREVIAR', ph: 'Maria da Silva Souza', coluna: true },
      { id: 'nusp', rotulo: 'N. USP', ph: '12345678', soDigitos: true },
      { id: 'programa', rotulo: 'PROGRAMA', ph: 'Matemática' },
      { id: 'nivel', rotulo: 'NÍVEL', alunos: true, sel: ['Mestrado', 'Doutorado'] },
      { id: 'tipo', rotulo: 'TIPO DE AUXÍLIO', alunos: true, sel: ['Participação em evento', 'Banca de exame ou defesa', 'Outro'] },
      { id: 'email', rotulo: 'E-MAIL', ph: 'maria.souza@ime.usp.br' },
      { id: 'evento', rotulo: 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', ph: 'XXV Congresso Brasileiro de Matemática', coluna: true },
      { id: 'periodo', rotulo: 'PERÍODO DO EVENTO, EXAME OU DEFESA', ph: '10 a 14/11/2025', linha: true },
      { id: 'cidade_evento', rotulo: 'CIDADE DO EVENTO, EXAME OU DEFESA', ph: 'Rio de Janeiro', linha: true },
      { id: 'estado_evento', rotulo: 'ESTADO DO EVENTO, EXAME OU DEFESA', ph: 'RJ', linha: true },
      { id: 'pais_evento', rotulo: 'PAÍS DO EVENTO, EXAME OU DEFESA', ph: 'Brasil', linha: true },
      { id: 'link', rotulo: 'LINK DO EVENTO, EXAME OU DEFESA', ph: 'https://eventomatematica.org', opcional: true, linha: true },
      { id: 'valor', rotulo: 'VALOR SOLICITADO (R$)', ph: '150000', formato: 'valor', linha: true },
      { id: 'detalhamento', rotulo: 'DETALHAMENTO DO PEDIDO', ph: 'Solicito auxílio para custear passagem, hospedagem e inscrição no congresso, fundamentais para a conclusão da minha pesquisa de doutorado.', area: true },
      { id: 'apresentacao', rotulo: 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', sel: ['Pôster', 'Apresentação oral', 'Outra', 'Não irá apresentar trabalho'] },
    ],
  },
  {
    titulo: 'ENDEREÇO DO SOLICITANTE',
    campos: [
      { id: 'nascimento', rotulo: 'DATA DE NASCIMENTO', ph: '01/02/1980', formato: 'data' },
      { id: 'logradouro', rotulo: 'LOGRADOURO', ph: 'Rua do Matão', coluna: true },
      { id: 'numero', rotulo: 'NÚMERO', ph: '1010', linha: true },
      { id: 'complemento', rotulo: 'COMPLEMENTO', ph: 'Apto 22, Bloco B', opcional: true, linha: true },
      { id: 'bairro', rotulo: 'BAIRRO', ph: 'Butantã', linha: true },
      { id: 'cep', rotulo: 'CEP', ph: '05508090', formato: 'cep', linha: true },
      { id: 'cidade', rotulo: 'CIDADE', ph: 'São Paulo', linha: true },
      { id: 'estado', rotulo: 'ESTADO', ph: 'SP', linha: true },
    ],
  },
  {
    titulo: 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
    campos: [
      { id: 'cpf', rotulo: 'CPF (SEPARADOS POR PONTOS E TRAÇO)', ph: '12345678909', formato: 'cpf', linha: true },
      { id: 'rg', rotulo: 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', ph: '12.345.678-9', linha: true },
      { id: 'banco', rotulo: 'NOME DO BANCO', ph: 'Banco do Brasil', linha: true },
      { id: 'agencia', rotulo: 'NÚMERO DA AGÊNCIA', ph: '1234', soDigitos: true, linha: true },
      { id: 'conta', rotulo: 'NÚMERO DA CONTA', ph: '12345-6', linha: true },
    ],
  },
];

function headerHTML() {
  return '<img src="assets/usp-logo.png" alt="Logotipo da Universidade de São Paulo">' +
    '<div class="marca">' +
    '<div class="marca-nome">Universidade de São Paulo</div>' +
    '<div class="marca-subs">Pós-Graduação do Instituto de Matemática e Estatística (IME-USP)</div>' +
    '</div>';
}
cabecalho.innerHTML = headerHTML();

function campoHTML(c) {
  const id = c.id;
  const rot = c.rotulo;
  const classe = 'campo' + (c.area || c.coluna ? ' grande' : '');
  let input;
  if (c.sel) {
    const opcoes = c.sel.map((o) => `<option value="${o}">${o}</option>`).join('');
    input = `<select id="f-${id}" name="${id}" required><option value="">Selecione ${rot}</option>${opcoes}</select>`;
  } else if (c.area) {
    input = `<textarea id="f-${id}" name="${id}" rows="2" placeholder="${c.ph}" required></textarea>`;
  } else {
    const extra = (c.soDigitos ? ' data-digitos="1"' : '') + (c.formato ? ` data-formato="${c.formato}"` : '');
    input = `<input id="f-${id}" name="${id}" type="text" placeholder="${c.ph}"${extra}${c.opcional ? '' : ' required'}>`;
  }
  return `<div class="${classe}"><label for="f-${id}">${rot}${c.opcional ? ' (opcional)' : ''}</label>${input}</div>`;
}

function blocoHTML(b) {
  const campos = b.campos.map((c) => campoHTML(c)).join('');
  return `<section class="bloco"><h2>${b.titulo}</h2><div class="grade">${campos}</div></section>`;
}

function formHTML(aba) {
  const blocos = BLOCOS.map((b) => blocoHTML(b))
    .join('')
    .replace(/<(section class="bloco"><h2>|<div class="grade">)/g, '$1');
  return `<form novalidate data-aba="${aba}">` +
    '<ul class="erros" role="alert" aria-live="assertive" hidden></ul>' +
    blocos +
    '<div class="rodape"><button type="submit" class="enviar">Enviar solicitação</button></div>' +
    '</form>';
}

function montarPainel(p, aba) {
  const html = formHTML(aba);
  p.innerHTML = html;
  const form = p.querySelector('form');
  const erros = form.querySelector('.erros');
  const blocos = [...form.querySelectorAll('.bloco')];
  const enviar = form.querySelector('.enviar');

  const limparErro = (el) => {
    if (el.name && el.name !== 'link' && el.name !== 'complemento') {
      erros.hidden = true;
      erros.textContent = '';
    }
  };

  form.querySelectorAll('input, select, textarea').forEach((el) => {
    el.addEventListener('input', () => limparErro(el));
    el.addEventListener('change', () => limparErro(el));
  });

  form.addEventListener('input', (e) => {
    const t = e.target;
    if (!t.dataset || !t.dataset.digitos) return;
    const limpo = t.value.replace(/\D/g, '');
    if (limpo !== t.value) t.value = limpo;
  });

  form.addEventListener('change', (e) => {
    const t = e.target;
    if (t.dataset && t.dataset.formato) aplicarFormato(t);
  });

  form.addEventListener('blur', (e) => {
    const t = e.target;
    if (t.dataset && t.dataset.formato) aplicarFormato(t);
  }, true);

  enviar.addEventListener('click', (e) => {
    e.preventDefault();
    coletar(aba, form, erros, blocos, enviar);
  });
}

function coletar(aba, form, erros, blocos, enviar) {
  erros.hidden = true;
  erros.textContent = '';
  const dados = {};
  form.querySelectorAll('input, select, textarea').forEach((el) => {
    dados[el.name] = el.value.trim();
  });
  if (aba !== 'alunos') {
    delete dados.nivel;
    delete dados.tipo;
  }
  enviar.disabled = true;
  fetch('/api/solicitacao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ aba: aba, dados: dados }),
  })
    .then((res) => res.json().then((json) => ({ status: res.status, json: json })))
    .then(({ status, json }) => {
      enviar.disabled = false;
      if (json.ok) {
        mostrarOficio(json.oficio, blocos, enviar);
      } else {
        erros.textContent = '';
        (json.erros || []).forEach((m) => {
          const li = document.createElement('li');
          li.textContent = m;
          erros.appendChild(li);
        });
        erros.hidden = false;
        erros.scrollIntoView({ block: 'nearest' });
      }
    })
    .catch(() => {
      enviar.disabled = false;
    });
}

function mostrarOficio(texto, blocos, enviar) {
  oficioEl.textContent = texto;
  blocos.forEach((b) => (b.hidden = true));
  enviar.hidden = true;
  confirmacao.classList.add('ativa');
  document.querySelectorAll('.painel').forEach((p) => p.classList.remove('ativa'));
  document.querySelector('.abas').style.visibility = 'hidden';
  cabecalho.scrollTop = 0;
}

function ocultarOficio() {
  document.querySelectorAll('.painel .erros').forEach((el) => {
    el.hidden = true;
    el.textContent = '';
  });
  document.querySelectorAll('.bloco').forEach((b) => (b.hidden = false));
  document.querySelectorAll('.enviar').forEach((b) => (b.hidden = false));
  document.querySelector('.abas').style.visibility = '';
  confirmacao.classList.remove('ativa');
  document
    .querySelector(`.painel[data-aba="${abaAtual}"]`)
    .classList.add('ativa');
}

function aplicarFormato(el) {
  const v = el.value;
  if (el.dataset.formato === 'valor') {
    const d = v.replace(/\D/g, '');
    if (!d) { el.value = ''; return; }
    const cent = parseInt(d, 10);
    const inteiro = Math.floor(cent / 100);
    const resto = cent % 100;
    el.value = 'R$ ' + String(inteiro).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + String(resto).padStart(2, '0');
  } else if (el.dataset.formato === 'cpf') {
    const d = v.replace(/\D/g, '').slice(0, 11);
    let r = d.slice(0, 3);
    if (d.length > 3) r += '.' + d.slice(3, 6);
    if (d.length > 6) r += '.' + d.slice(6, 9);
    if (d.length > 9) r += '-' + d.slice(9, 11);
    el.value = r;
  } else if (el.dataset.formato === 'cep') {
    const d = v.replace(/\D/g, '').slice(0, 8);
    el.value = d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  } else if (el.dataset.formato === 'data') {
    const d = v.replace(/\D/g, '').slice(0, 8);
    let r = d.slice(0, 2);
    if (d.length > 2) r += '/' + d.slice(2, 4);
    if (d.length > 4) r += '/' + d.slice(4, 8);
    el.value = r;
  }
}

let abaAtual = 'alunos';
abas.forEach((btn) => {
  btn.addEventListener('click', () => {
    abaAtual = btn.dataset.aba;
    abas.forEach((b) => {
      const ativa = b === btn;
      b.classList.toggle('ativa', ativa);
      b.setAttribute('aria-selected', ativa ? 'true' : 'false');
    });
    paineis.forEach((p) => p.classList.toggle('ativa', p.dataset.aba === btn.dataset.aba));
  });
});

document.querySelector('.voltar').addEventListener('click', ocultarOficio);

paineis.forEach((p) => montarPainel(p, p.dataset.aba));
