/* Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP */

'use strict';

var FORMS = {
  alunos: document.getElementById('form-alunos'),
  docentes: document.getElementById('form-docentes')
};

function ativarAba(nome) {
  document.querySelectorAll('.aba').forEach(function (botao) {
    botao.classList.toggle('ativa', botao.dataset.aba === nome);
  });
  Object.keys(FORMS).forEach(function (aba) {
    FORMS[aba].hidden = aba !== nome;
  });
}

document.querySelectorAll('.aba').forEach(function (botao) {
  botao.addEventListener('click', function () {
    ativarAba(botao.dataset.aba);
  });
});

/* Campos que se formatam sozinhos, no momento em que o usuário sai deles */

document.querySelectorAll('[data-formato]').forEach(function (campo) {
  campo.addEventListener('blur', function () {
    fetch('/formatar/' + campo.dataset.formato + '?digitado=' + encodeURIComponent(campo.value))
      .then(function (resposta) { return resposta.json(); })
      .then(function (dados) { campo.value = dados.formatado; });
  });
});

function digitos(texto) {
  return texto.split('').filter(function (caractere) {
    return caractere >= '0' && caractere <= '9';
  }).join('');
}

function coletar(form) {
  var dados = {};
  form.querySelectorAll('[name]').forEach(function (campo) {
    dados[campo.name] = campo.value;
  });
  ['valor', 'cpf', 'cep', 'nascimento'].forEach(function (nome) {
    if (Object.prototype.hasOwnProperty.call(dados, nome)) {
      dados[nome] = digitos(dados[nome]);
    }
  });
  return dados;
}

function mostrarErros(form, erros) {
  var caixa = form.querySelector('.erros');
  caixa.textContent = '';
  erros.forEach(function (mensagem) {
    var linha = document.createElement('p');
    linha.textContent = mensagem;
    caixa.appendChild(linha);
  });
  caixa.hidden = false;
}

function mostrarConfirmacao(corpo) {
  document.querySelector('.abas').hidden = true;
  Object.keys(FORMS).forEach(function (aba) {
    FORMS[aba].hidden = true;
  });
  document.getElementById('titulo-confirmacao').textContent = corpo.titulo;
  document.getElementById('oficio').textContent = corpo.oficio;
  document.getElementById('confirmacao').hidden = false;
}

Object.keys(FORMS).forEach(function (aba) {
  FORMS[aba].addEventListener('submit', function (evento) {
    evento.preventDefault();
    var form = evento.target;
    form.querySelector('.erros').hidden = true;
    var carga = coletar(form);
    carga.aba = form.dataset.aba;
    fetch('/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(carga)
    })
      .then(function (resposta) {
        return resposta.json().then(function (corpo) {
          return { valido: resposta.ok, corpo: corpo };
        });
      })
      .then(function (resultado) {
        if (resultado.valido) {
          mostrarConfirmacao(resultado.corpo);
        } else {
          mostrarErros(form, resultado.corpo.erros);
        }
      });
  });
});
