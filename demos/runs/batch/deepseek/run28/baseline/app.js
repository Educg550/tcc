(function () {
  'use strict';

  var mascaras = {
    valor: function (valor) {
      var digitos = valor.replace(/\D/g, '');
      if (!digitos) { return ''; }
      var centavos = parseInt(digitos, 10);
      return 'R$ ' + (centavos / 100).toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });
    },
    cpf: function (valor) {
      var digitos = valor.replace(/\D/g, '').slice(0, 11);
      return digitos
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
        .replace(/(\d{3})\.(\d{3})\.(\d{3})(\d)/, '$1.$2.$3-$4');
    },
    cep: function (valor) {
      var digitos = valor.replace(/\D/g, '').slice(0, 8);
      return digitos.replace(/^(\d{5})(\d)/, '$1-$2');
    },
    data: function (valor) {
      var digitos = valor.replace(/\D/g, '').slice(0, 8);
      return digitos
        .replace(/^(\d{2})(\d)/, '$1/$2')
        .replace(/^(\d{2})\/(\d{2})(\d)/, '$1/$2/$3');
    }
  };

  document.querySelectorAll('input[data-mask]').forEach(function (campo) {
    campo.addEventListener('blur', function () {
      campo.value = mascaras[campo.dataset.mask](campo.value);
    });
  });

  var abas = document.querySelectorAll('.aba');
  var paineis = document.querySelectorAll('.painel');

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) {
        var ativa = outra === aba;
        outra.classList.toggle('ativa', ativa);
        outra.setAttribute('aria-selected', ativa ? 'true' : 'false');
      });
      paineis.forEach(function (painel) {
        painel.classList.toggle('ativo', painel.dataset.aba === aba.dataset.aba);
      });
    });
  });

  paineis.forEach(function (painel) {
    painel.addEventListener('submit', function (evento) {
      evento.preventDefault();

      var dados = { aba: painel.dataset.aba };
      new FormData(painel).forEach(function (valor, chave) {
        dados[chave] = valor.trim();
      });

      var erros = painel.querySelector('.erros');

      fetch('/api/solicitar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (resposta) {
          if (resposta.valido) {
            document.getElementById('oficio').textContent = resposta.oficio;
            document.getElementById('formularios').hidden = true;
            document.getElementById('confirmacao').hidden = false;
            window.scrollTo(0, 0);
          } else {
            erros.textContent = resposta.erros.join('\n');
            erros.hidden = false;
          }
        });
    });
  });
})();
