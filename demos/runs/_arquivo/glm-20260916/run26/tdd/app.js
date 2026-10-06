(function () {
  'use strict';

  function digitos(valor) {
    return String(valor).replace(/\D+/g, '');
  }

  function formatarMoeda(valor) {
    var d = digitos(valor).replace(/^0+(?=\d)/, '');
    if (!d) return '';
    while (d.length < 3) d = '0' + d;
    var centavos = d.slice(-2);
    var inteira = d.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + inteira + ',' + centavos;
  }

  function formatarCpf(valor) {
    var d = digitos(valor).slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + '.' + d.slice(3);
    return d;
  }

  function formatarCep(valor) {
    var d = digitos(valor).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }

  function formatarData(valor) {
    var d = digitos(valor).slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + '/' + d.slice(2);
    return d;
  }

  var formatos = { moeda: formatarMoeda, cpf: formatarCpf, cep: formatarCep, data: formatarData };

  Array.prototype.forEach.call(document.querySelectorAll('[data-fmt]'), function (campo) {
    campo.addEventListener('blur', function () {
      campo.value = formatos[campo.getAttribute('data-fmt')](campo.value);
    });
  });

  var abas = Array.prototype.slice.call(document.querySelectorAll('.aba'));
  var formularios = Array.prototype.slice.call(document.querySelectorAll('.formulario'));

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) { outra.classList.toggle('ativa', outra === aba); });
      formularios.forEach(function (form) {
        form.hidden = form.getAttribute('data-aba') !== aba.getAttribute('data-aba');
      });
    });
  });

  formularios.forEach(function (formulario) {
    formulario.addEventListener('submit', function (evento) {
      evento.preventDefault();
      var dados = {};
      Array.prototype.forEach.call(new FormData(formulario).entries(), function (par) {
        dados[par[0]] = par[1];
      });
      var aviso = formulario.querySelector('.erros');
      fetch('/api/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/' },
        body: JSON.stringify(dados)
      }).then(function (resposta) { return resposta.(); }).then(function (r) {
        if (r.ok) {
          document.getElementById('conteudo').hidden = true;
          document.getElementById('oficio').textContent = r.oficio;
          document.getElementById('confirmacao').hidden = false;
          window.scrollTo(0, 0);
        } else {
          aviso.textContent = (r.erros || []).join('\n');
          aviso.hidden = false;
        }
      });
    });
  });
})();
