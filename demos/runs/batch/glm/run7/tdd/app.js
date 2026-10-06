(function () {
  'use strict';

  function digitos(s) {
    return (s || '').replace(/\D/g, '');
  }

  function milhar(s) {
    return s.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  }

  var FORMATOS = {
    valor: function (d) {
      if (!d) { return ''; }
      var cent = ('0' + d).slice(-2);
      var reais = String(Math.floor(parseInt(d, 10) / 100));
      return 'R$ ' + milhar(reais) + ',' + cent;
    },
    cpf: function (d) {
      return d.length === 11
        ? d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9)
        : d;
    },
    cep: function (d) {
      return d.length === 8 ? d.slice(0, 5) + '-' + d.slice(5) : d;
    },
    data_nascimento: function (d) {
      return d.length === 8 ? d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4) : d;
    }
  };

  Object.keys(FORMATOS).forEach(function (nome) {
    var formata = FORMATOS[nome];
    document.querySelectorAll('input[name="' + nome + '"]').forEach(function (campo) {
      campo.addEventListener('blur', function () {
        var d = digitos(campo.value);
        if (d) { campo.value = formata(d); }
      });
    });
  });

  var abas = document.querySelectorAll('.aba[data-aba]');
  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (b) { b.classList.toggle('ativa', b === aba); });
      document.querySelectorAll('.formulario').forEach(function (form) {
        form.classList.toggle('oculta', form.getAttribute('data-aba') !== aba.getAttribute('data-aba'));
      });
    });
  });
})();
