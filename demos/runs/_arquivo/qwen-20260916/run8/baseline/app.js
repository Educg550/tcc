'use strict';

var CAMPOS = [
  { bloco: 'SOLICITANTE E EVENTO' },
  { nome: 'nome', rotulo: 'NOME COMPLETO - SEM ABREVIAR', tipo: 'text', ph: 'Maria da Silva Souza', cols: 4 },
  { nome: 'nusp', rotulo: 'N. USP', tipo: 'text', ph: '12345678', cols: 2 },
  { nome: 'programa', rotulo: 'PROGRAMA', tipo: 'text', ph: 'Matemática', cols: 3 },
  { nome: 'nivel', rotulo: 'NÍVEL', tipo: 'select', opcoes: ['Mestrado', 'Doutorado'], cols: 2, alunos: true },
  { nome: 'tipo_auxilio', rotulo: 'TIPO DE AUXÍLIO', tipo: 'select', opcoes: ['Participação em evento', 'Banca de exame ou defesa', 'Outro'], cols: 3, alunos: true },
  { nome: 'email', rotulo: 'E-MAIL', tipo: 'email', ph: 'maria@ime.usp.br', cols: 3 },
  { nome: 'nome_evento', rotulo: 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', tipo: 'text', ph: 'XII Congresso Brasileiro de Matemática', cols: 4 },
  { nome: 'periodo', rotulo: 'PERÍODO DO EVENTO, EXAME OU DEFESA', tipo: 'text', ph: '15 a 20 de outubro de 2024', cols: 3 },
  { nome: 'cidade_evento', rotulo: 'CIDADE DO EVENTO, EXAME OU DEFESA', tipo: 'text', ph: 'São Paulo', cols: 3 },
  { nome: 'estado_evento', rotulo: 'ESTADO DO EVENTO, EXAME OU DEFESA', tipo: 'text', ph: 'SP', cols: 2 },
  { nome: 'pais_evento', rotulo: 'PAÍS DO EVENTO, EXAME OU DEFESA', tipo: 'text', ph: 'Brasil', cols: 2 },
  { nome: 'link', rotulo: 'LINK DO EVENTO, EXAME OU DEFESA', tipo: 'text', ph: 'https://evento.org.br', cols: 4, opcional: true },
  { nome: 'valor', rotulo: 'VALOR SOLICITADO (R$)', tipo: 'text', ph: 'R$ 1.500,00', cols: 2, formato: 'valor' },
  { nome: 'detalhamento', rotulo: 'DETALHAMENTO DO PEDIDO', tipo: 'textarea', ph: 'Descreva o pedido, justificando a solicitação do auxílio', cols: 8 },
  { nome: 'apresentacao', rotulo: 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', tipo: 'select', opcoes: ['Pôster', 'Apresentação oral', 'Outra', 'Não irá apresentar trabalho'], cols: 4 },
  { bloco: 'ENDEREÇO DO SOLICITANTE' },
  { nome: 'nascimento', rotulo: 'DATA DE NASCIMENTO', tipo: 'text', ph: 'dd/mm/aaaa', cols: 2, formato: 'data' },
  { nome: 'logradouro', rotulo: 'LOGRADOURO', tipo: 'text', ph: 'Rua do Matão', cols: 4 },
  { nome: 'numero', rotulo: 'NÚMERO', tipo: 'text', ph: '1010', cols: 2 },
  { nome: 'complemento', rotulo: 'COMPLEMENTO', tipo: 'text', ph: 'Apto 52', cols: 2, opcional: true },
  { nome: 'bairro', rotulo: 'BAIRRO', tipo: 'text', ph: 'Butantã', cols: 2 },
  { nome: 'cep', rotulo: 'CEP', tipo: 'text', ph: '05508-090', cols: 2, formato: 'cep' },
  { nome: 'cidade', rotulo: 'CIDADE', tipo: 'text', ph: 'São Paulo', cols: 4 },
  { nome: 'estado', rotulo: 'ESTADO', tipo: 'text', ph: 'SP', cols: 2 },
  { bloco: 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO' },
  { nome: 'cpf', rotulo: 'CPF (SEPARADOS POR PONTOS E TRAÇO)', tipo: 'text', ph: '123.456.789-09', cols: 3, formato: 'cpf' },
  { nome: 'rg', rotulo: 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', tipo: 'text', ph: '12.345.678-9', cols: 3 },
  { nome: 'banco', rotulo: 'NOME DO BANCO', tipo: 'text', ph: 'Banco do Brasil', cols: 3 },
  { nome: 'agencia', rotulo: 'NÚMERO DA AGÊNCIA', tipo: 'text', ph: '1234', cols: 2 },
  { nome: 'conta', rotulo: 'NÚMERO DA CONTA', tipo: 'text', ph: '12345-6', cols: 2 }
];

function apenasDigitos(v) {
  return String(v).replace(/\D/g, '');
}

function grupoMilhar(n) {
  var s = String(n).replace(/\d+/, function (x) {
    return x.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  });
  return s;
}

function formataMoeda(v) {
  var d = apenasDigitos(v).replace(/^0+/, '');
  if (!d) return '';
  if (d.length < 3) d = d.padStart(3, '0');
  var inteiro = d.slice(0, -2).replace(/^0+/, '') || '0';
  return 'R$ ' + grupoMilhar(inteiro) + ',' + d.slice(-2);
}

function formataCpf(v) {
  var d = apenasDigitos(v).slice(0, 11);
  return d.replace(/(\d{3})(\d{0,3})(\d{0,3})(\d{0,2})/, function (m, a, b, c, e) {
    var r = a;
    if (b) r += '.' + b;
    if (c) r += '.' + c;
    if (e) r += '-' + e;
    return r;
  });
}

function formataCep(v) {
  var d = apenasDigitos(v).slice(0, 8);
  if (d.length <= 5) return d;
  return d.slice(0, 5) + '-' + d.slice(5);
}

function formataData(v) {
  var d = apenasDigitos(v).slice(0, 8);
  return d.replace(/(\d{2})(\d{0,2})(\d{0,4})/, function (m, a, b, c) {
    var r = a;
    if (b) r += '/' + b;
    if (c) r += '/' + c;
    return r;
  });
}

function formatar(campo, valor) {
  if (campo.formato === 'valor') return formataMoeda(valor);
  if (campo.formato === 'cpf') return formataCpf(valor);
  if (campo.formato === 'cep') return formataCep(valor);
  if (campo.formato === 'data') return formataData(valor);
  return valor;
}

function montaFormulario(form, aba) {
  var camposDiv = document.createElement('div');
  camposDiv.className = 'campos';
  form.appendChild(camposDiv);

  var inputs = {};
  CAMPOS.forEach(function (c) {
    if (c.bloco) {
      var titulo = document.createElement('h2');
      titulo.className = 'bloco';
      titulo.textContent = c.bloco;
      camposDiv.appendChild(titulo);
      return;
    }
    if (c.alunos && aba === 'DOCENTES') return;

    var label = document.createElement('label');
    var texto = document.createElement('span');
    texto.textContent = c.rotulo;
    label.appendChild(texto);

    var el;
    if (c.tipo === 'select') {
      el = document.createElement('select');
      var vazio = document.createElement('option');
      vazio.value = '';
      vazio.textContent = 'Selecione';
      el.appendChild(vazio);
      c.opcoes.forEach(function (op) {
        var o = document.createElement('option');
        o.value = op;
        o.textContent = op;
        el.appendChild(o);
      });
    } else if (c.tipo === 'textarea') {
      el = document.createElement('textarea');
      el.placeholder = c.ph;
      el.rows = 2;
    } else {
      el = document.createElement('input');
      el.type = c.tipo;
      el.placeholder = c.ph;
    }
    el.name = c.nome;
    el.id = aba + '_' + c.nome;
    label.setAttribute('for', el.id);
    el.setAttribute('aria-label', c.rotulo);
    if (!c.opcional) el.setAttribute('aria-required', 'true');

    if (c.formato === 'valor') el.inputMode = 'numeric';
    if (c.formato) {
      el.addEventListener('input', function () {
        var pos = el.value.length;
        el.value = formatar(c, el.value);
        if (el.setSelectionRange) {
          try { el.setSelectionRange(pos, pos); } catch (e) {}
        }
      });
      el.addEventListener('blur', function () {
        el.value = formatar(c, el.value);
      });
    }

    var wrap = document.createElement('div');
    wrap.className = 'campo c' + c.cols;
    wrap.appendChild(label);
    wrap.appendChild(el);
    camposDiv.appendChild(wrap);
    inputs[c.nome] = el;
  });

  var rodape = document.createElement('div');
  rodape.className = 'rodape';
  var erros = document.createElement('div');
  erros.className = 'erros';
  erros.hidden = true;
  var botao = document.createElement('button');
  botao.type = 'submit';
  botao.id = 'btn';
  botao.textContent = 'Enviar solicitação';
  rodape.appendChild(erros);
  rodape.appendChild(botao);
  camposDiv.appendChild(rodape);

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    enviaSolicitacao(form, aba, inputs, erros);
  });

  return inputs;
}

async function enviaSolicitacao(form, aba, inputs, erros) {
  var dados = new FormData(form);
  dados.append('aba', aba);

  var resposta = await fetch('/solicitacao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
    body: new URLSearchParams(dados).toString()
  });

  var json = await resposta.json();

  if (!json.ok) {
    erros.textContent = '';
    json.erros.forEach(function (m) {
      var linha = document.createElement('div');
      linha.className = 'erro';
      linha.textContent = m;
      erros.appendChild(linha);
    });
    erros.hidden = false;
    return;
  }

  document.getElementById('pagina').hidden = true;
  document.getElementById('oficio').textContent = json.oficio;
  document.getElementById('confirmacao').hidden = false;
  window.scrollTo(0, 0);
}

function mostra(aba) {
  document.querySelectorAll('.aba').forEach(function (a) {
    var ativo = a.dataset.tab === aba;
    a.classList.toggle('ativa', ativo);
    a.setAttribute('aria-selected', ativo ? 'true' : 'false');
  });
  document.querySelectorAll('.formulario').forEach(function (f) {
    f.hidden = f.dataset.tab !== aba;
  });
  document.getElementById('pagina').hidden = false;
  document.getElementById('confirmacao').hidden = true;
}

document.querySelectorAll('.aba').forEach(function (a) {
  a.addEventListener('click', function () { mostra(a.dataset.tab); });
});

montaFormulario(document.getElementById('form-ALUNOS'), 'ALUNOS');
montaFormulario(document.getElementById('form-DOCENTES'), 'DOCENTES');
mostra('ALUNOS');
