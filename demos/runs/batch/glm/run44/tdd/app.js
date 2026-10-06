/* Comportamento de tela do formulário de auxílio financeiro - Pós-Graduação do IME-USP. */
'use strict';

var botoes = [].slice.call(document.querySelectorAll('.tab-button'));
var paineis = {
  alunos: document.getElementById('aba-alunos'),
  docentes: document.getElementById('aba-docentes')
};

/* Abas: troca sem recarregar a página e sem perder o que já foi digitado. */
function ativarAba(nome) {
  botoes.forEach(function (botao) {
    botao.classList.toggle('active', botao.getAttribute('data-aba') === nome);
  });
  Object.keys(paineis).forEach(function (aba) {
    paineis[aba].classList.toggle('ativo', aba === nome);
  });
}

botoes.forEach(function (botao) {
  botao.addEventListener('click', function () {
    ativarAba(botao.getAttribute('data-aba'));
  });
});

/* Campos que se formatam sozinhos: o usuário digita dígitos, a pontuação é da aplicação. */
function soDigitos(valor) {
  return (valor || '').replace(/[^0-9]/g, '');
}

function formatarMoeda(valor) {
  var digitos = soDigitos(valor);
  if (!digitos) { return ''; }
  var centavos = parseInt(digitos, 10);
  return 'R$ ' + (centavos / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatarCpf(valor) {
  var d = soDigitos(valor).slice(0, 11);
  if (d.length > 9) { return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9); }
  if (d.length > 6) { return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9); }
  if (d.length > 3) { return d.slice(0, 3) + '.' + d.slice(3, 6); }
  return d;
}

function formatarCep(valor) {
  var d = soDigitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(valor) {
  var d = soDigitos(valor).slice(0, 8);
  if (d.length > 4) { return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4); }
  if (d.length > 2) { return d.slice(0, 2) + '/' + d.slice(2, 4); }
  return d;
}

var formatadores = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData
};

[].forEach.call(document.querySelectorAll('[data-formato]'), function (campo) {
  var formatar = formatadores[campo.getAttribute('data-formato')];
  var aplicar = function () { campo.value = formatar(campo.value); };
  campo.addEventListener('input', aplicar);
  campo.addEventListener('blur', aplicar);
});

/* Envio: quem decide se a solicitação é válida é o backend. */
function coletarDados(form) {
  var dados = { tipo: form.getAttribute('data-tipo') };
  [].forEach.call(form.elements, function (elemento) {
    if (elemento.name) { dados[elemento.name] = elemento.value; }
  });
  return dados;
}

function mostrarErros(form, erros) {
  var caixa = document.getElementById('erros-' + form.getAttribute('data-tipo'));
  caixa.textContent = '';
  erros.forEach(function (mensagem) {
    var linha = document.createElement('p');
    linha.textContent = mensagem;
    caixa.appendChild(linha);
  });
  caixa.style.display = 'block';
}

function mostrarConfirmacao(oficio) {
  document.querySelector('.abas').style.display = 'none';
  Object.keys(paineis).forEach(function (aba) {
    paineis[aba].classList.remove('ativo');
    paineis[aba].style.display = 'none';
  });
  var fimDoTitulo = oficio.indexOf('\n\n');
  document.getElementById('titulo-confirmacao').textContent = oficio.slice(0, fimDoTitulo);
  document.getElementById('oficio').textContent = oficio.slice(fimDoTitulo + 2);
  document.getElementById('confirmacao').classList.remove('oculto');
  window.scrollTo(0, 0);
}

[].forEach.call(document.querySelectorAll('form'), function (form) {
  form.addEventListener('submit', function (evento) {
    evento.preventDefault();
    fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(coletarDados(form))
    })
      .then(function (resposta) { return resposta.json(); })
      .then(function (corpo) {
        if (corpo.valido) {
          mostrarConfirmacao(corpo.oficio);
        } else {
          mostrarErros(form, corpo.erros || []);
        }
      });
  });
});
