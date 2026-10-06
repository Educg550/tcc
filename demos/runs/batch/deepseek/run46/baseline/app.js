(function () {
  'use strict';

  function soDigitos(v) {
    return String(v).replace(/\D/g, '');
  }

  function mascaraValor(v) {
    var d = soDigitos(v);
    if (!d) { return ''; }
    var n = parseInt(d, 10);
    var reais = String(Math.floor(n / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + reais + ',' + String(n % 100).padStart(2, '0');
  }

  function mascaraCPF(v) {
    var d = soDigitos(v).slice(0, 11);
    var s = d.slice(0, 3);
    if (d.length > 3) { s += '.' + d.slice(3, 6); }
    if (d.length > 6) { s += '.' + d.slice(6, 9); }
    if (d.length > 9) { s += '-' + d.slice(9); }
    return s;
  }

  function mascaraCEP(v) {
    var d = soDigitos(v).slice(0, 8);
    var s = d.slice(0, 5);
    if (d.length > 5) { s += '-' + d.slice(5); }
    return s;
  }

  function mascaraData(v) {
    var d = soDigitos(v).slice(0, 8);
    var s = d.slice(0, 2);
    if (d.length > 2) { s += '/' + d.slice(2, 4); }
    if (d.length > 4) { s += '/' + d.slice(4); }
    return s;
  }

  var mascarados = [
    ['valor', mascaraValor],
    ['cpf', mascaraCPF],
    ['cep', mascaraCEP],
    ['data_nascimento', mascaraData]
  ];

  var abas = document.querySelectorAll('.aba');
  var paineis = document.querySelectorAll('.painel');

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) { outra.classList.toggle('ativa', outra === aba); });
      paineis.forEach(function (painel) {
        painel.classList.toggle('oculto', painel.id !== 'painel-' + aba.dataset.aba);
      });
    });
  });

  document.querySelectorAll('form').forEach(function (form) {
    mascarados.forEach(function (par) {
      var campo = form.elements[par[0]];
      if (campo) {
        campo.addEventListener('blur', function () { campo.value = par[1](campo.value); });
      }
    });

    form.addEventListener('submit', function (evento) {
      evento.preventDefault();

      var aba = form.dataset.aba;
      var campos = {};
      new FormData(form).forEach(function (valor, nome) { campos[nome] = valor; });

      fetch('/api/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ aba: aba, campos: campos })
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (dados) {
          var erros = document.getElementById('erros-' + aba);
          if (dados.ok) {
            erros.textContent = '';
            document.getElementById('oficio').textContent = dados.oficio;
            document.getElementById('formulario').classList.add('oculto');
            document.getElementById('confirmacao').classList.remove('oculto');
            window.scrollTo(0, 0);
          } else {
            erros.textContent = dados.erros.join('\n');
          }
        });
    });
  });
})();
