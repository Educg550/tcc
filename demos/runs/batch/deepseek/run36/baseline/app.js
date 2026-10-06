(function () {
  'use strict';

  var abas = document.querySelectorAll('.aba');
  var paineis = document.querySelectorAll('.painel');

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (item) {
        var ativa = item === aba;
        item.classList.toggle('ativa', ativa);
        item.setAttribute('aria-selected', ativa ? 'true' : 'false');
      });
      paineis.forEach(function (painel) {
        painel.classList.toggle('ativa', painel.dataset.aba === aba.dataset.aba);
      });
    });
  });

  function somenteDigitos(valor) {
    return (valor || '').replace(/\D/g, '');
  }

  function formatarValor(valor) {
    var digitos = somenteDigitos(valor).replace(/^0+(?=\d)/, '');
    if (!digitos) return '';
    digitos = digitos.padStart(3, '0');
    var centavos = digitos.slice(-2);
    var reais = digitos.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + reais + ',' + centavos;
  }

  function formatarCpf(valor) {
    var d = somenteDigitos(valor).slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + '.' + d.slice(3);
    return d;
  }

  function formatarCep(valor) {
    var d = somenteDigitos(valor).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }

  function formatarData(valor) {
    var d = somenteDigitos(valor).slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
    return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  }

  var formatadores = {
    valor: formatarValor,
    cpf: formatarCpf,
    cep: formatarCep,
    data: formatarData
  };

  document.querySelectorAll('[data-formatar]').forEach(function (campo) {
    campo.addEventListener('blur', function () {
      campo.value = formatadores[campo.dataset.formatar](campo.value);
    });
  });

  document.querySelectorAll('form.painel').forEach(function (form) {
    form.addEventListener('submit', function (evento) {
      evento.preventDefault();

      var dados = {};
      new FormData(form).forEach(function (valor, chave) { dados[chave] = valor; });
      dados.aba = form.dataset.aba;

      var caixaErros = form.querySelector('.erros');

      fetch('/api/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      }).then(function (resposta) {
        return resposta.json();
      }).then(function (resultado) {
        var erros = resultado.erros || [];
        if (erros.length) {
          caixaErros.textContent = erros.join('\n');
          caixaErros.hidden = false;
          return;
        }
        caixaErros.hidden = true;
        document.getElementById('oficio').textContent = resultado.oficio;
        document.getElementById('confirmacao').hidden = false;
        document.querySelector('.abas').hidden = true;
        document.querySelectorAll('form.painel').forEach(function (painel) {
          painel.classList.remove('ativa');
        });
      });
    });
  });
})();
