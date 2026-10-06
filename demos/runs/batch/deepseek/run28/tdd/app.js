(function () {
  'use strict';

  function digitos(texto) {
    return texto.replace(/\D/g, '');
  }

  function formatarMoeda(centavos) {
    var reais = Math.floor(centavos / 100);
    var resto = String(centavos % 100).padStart(2, '0');
    var milhares = String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + milhares + ',' + resto;
  }

  function mascaraValor(valor) {
    var apenasDigitos = digitos(valor);
    return apenasDigitos ? formatarMoeda(Number(apenasDigitos)) : '';
  }

  function mascaraCpf(valor) {
    var d = digitos(valor).slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + '.' + d.slice(3);
    return d;
  }

  function mascaraCep(valor) {
    var d = digitos(valor).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }

  function mascaraData(valor) {
    var d = digitos(valor).slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + '/' + d.slice(2);
    return d;
  }

  var MASCARAS = {
    valor: mascaraValor,
    cpf: mascaraCpf,
    cep: mascaraCep,
    data_nascimento: mascaraData,
  };

  document.querySelectorAll('[data-mascara]').forEach(function (campo) {
    campo.addEventListener('blur', function () {
      campo.value = MASCARAS[campo.dataset.mascara](campo.value);
    });
  });

  var abas = document.querySelectorAll('.aba');
  var paineis = {
    alunos: document.getElementById('form-alunos'),
    docentes: document.getElementById('form-docentes'),
  };
  var confirmacao = document.getElementById('confirmacao');
  var oficio = document.getElementById('oficio');

  function mostrarAba(nome) {
    abas.forEach(function (aba) {
      var ativa = aba.dataset.aba === nome;
      aba.classList.toggle('ativa', ativa);
      aba.setAttribute('aria-selected', ativa ? 'true' : 'false');
    });
    Object.keys(paineis).forEach(function (chave) {
      paineis[chave].hidden = chave !== nome;
    });
  }

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      mostrarAba(aba.dataset.aba);
    });
  });

  function mostrarErros(caixa, mensagens) {
    caixa.textContent = '';
    mensagens.forEach(function (mensagem) {
      var item = document.createElement('p');
      item.textContent = mensagem;
      caixa.appendChild(item);
    });
    caixa.hidden = false;
  }

  document.querySelectorAll('form.solicitacao').forEach(function (formulario) {
    formulario.addEventListener('submit', function (evento) {
      evento.preventDefault();
      var dados = Object.fromEntries(new FormData(formulario).entries());
      dados.aba = formulario.dataset.aba;
      fetch('/api/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados),
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (corpo) {
          var caixa = formulario.querySelector('.erros');
          if (corpo.erros && corpo.erros.length) {
            mostrarErros(caixa, corpo.erros);
            return;
          }
          caixa.textContent = '';
          caixa.hidden = true;
          oficio.textContent = corpo.oficio;
          Object.keys(paineis).forEach(function (chave) {
            paineis[chave].hidden = true;
          });
          document.querySelector('.abas').hidden = true;
          confirmacao.hidden = false;
        });
    });
  });
})();
