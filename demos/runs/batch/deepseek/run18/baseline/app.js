(function () {
  'use strict';

  var abas = document.querySelectorAll('.tab');
  var formularios = document.querySelectorAll('#form-view form');

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) {
        outra.classList.toggle('active', outra === aba);
      });
      formularios.forEach(function (form) {
        form.hidden = form.dataset.aba !== aba.dataset.tab;
      });
    });
  });

  function digitos(valor) {
    return (valor || '').replace(/\D/g, '');
  }

  function separaMilhar(numero) {
    return numero.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  }

  function formataValor(valor) {
    var d = digitos(valor);
    if (d === '') return '';
    var centavos = d.replace(/^0+(?=\d)/, '');
    var reais = centavos.length > 2 ? centavos.slice(0, -2) : '0';
    var resto = centavos.padStart(2, '0').slice(-2);
    return 'R$ ' + separaMilhar(reais) + ',' + resto;
  }

  function formataCPF(valor) {
    var d = digitos(valor).slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + '.' + d.slice(3);
    return d;
  }

  function formataCEP(valor) {
    var d = digitos(valor).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }

  function formataData(valor) {
    var d = digitos(valor).slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + '/' + d.slice(2);
    return d;
  }

  var formatadores = { valor: formataValor, cpf: formataCPF, cep: formataCEP, data: formataData };

  document.querySelectorAll('[data-mask]').forEach(function (campo) {
    campo.addEventListener('blur', function () {
      var formatar = formatadores[campo.dataset.mask];
      if (formatar) campo.value = formatar(campo.value);
    });
  });

  formularios.forEach(function (form) {
    form.addEventListener('submit', function (evento) {
      evento.preventDefault();

      var campos = {};
      form.querySelectorAll('[name]').forEach(function (campo) {
        campos[campo.name] = campo.value.trim();
      });

      fetch('/api/solicitar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ aba: form.dataset.aba, campos: campos })
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (dados) {
          var erros = form.querySelector('.erros');

          if (!dados.ok) {
            erros.textContent = '';
            dados.erros.forEach(function (mensagem) {
              var linha = document.createElement('div');
              linha.textContent = mensagem;
              erros.appendChild(linha);
            });
            erros.hidden = false;
            return;
          }

          erros.hidden = true;
          document.querySelector('.tabs').hidden = true;
          document.getElementById('oficio').textContent = dados.oficio;
          document.getElementById('form-view').hidden = true;
          document.getElementById('conf-view').hidden = false;
        });
    });
  });
})();
