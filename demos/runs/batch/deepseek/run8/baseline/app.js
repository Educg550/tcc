(function () {
  'use strict';

  function apenasDigitos(valor) {
    return valor.replace(/[^0-9]/g, '');
  }

  function formatarMoeda(valor) {
    var digitos = apenasDigitos(valor);
    if (!digitos) return '';
    var centavos = parseInt(digitos, 10);
    var reais = Math.floor(centavos / 100);
    var resto = String(centavos % 100).padStart(2, '0');
    var inteiro = String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + inteiro + ',' + resto;
  }

  function formatarCPF(valor) {
    var d = apenasDigitos(valor).slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.slice(0, 3) + '.' + d.slice(3);
    if (d.length <= 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  }

  function formatarCEP(valor) {
    var d = apenasDigitos(valor).slice(0, 8);
    if (d.length <= 5) return d;
    return d.slice(0, 5) + '-' + d.slice(5);
  }

  function formatarData(valor) {
    var d = apenasDigitos(valor).slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
    return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  }

  var formatadores = {
    valor: formatarMoeda,
    cpf: formatarCPF,
    cep: formatarCEP,
    data_nascimento: formatarData
  };

  document.querySelectorAll('input[name]').forEach(function (input) {
    var formatar = formatadores[input.name];
    if (formatar) {
      input.addEventListener('blur', function () {
        input.value = formatar(input.value);
      });
    }
  });

  var abas = Array.prototype.slice.call(document.querySelectorAll('.aba'));

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) {
        var ativa = outra === aba;
        outra.classList.toggle('ativa', ativa);
        outra.setAttribute('aria-selected', ativa ? 'true' : 'false');
        document.getElementById(outra.getAttribute('aria-controls')).classList.toggle('oculto', !ativa);
      });
    });
  });

  var principal = document.getElementById('principal');
  var confirmacao = document.getElementById('confirmacao');
  var oficio = document.getElementById('oficio');

  document.querySelectorAll('form').forEach(function (form) {
    form.addEventListener('submit', function (evento) {
      evento.preventDefault();

      var areaErros = form.querySelector('.erros');
      areaErros.innerHTML = '';

      var dados = Object.fromEntries(new FormData(form).entries());
      dados.aba = form.dataset.aba;

      fetch('/api/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (resultado) {
          if (resultado.erros && resultado.erros.length) {
            resultado.erros.forEach(function (mensagem) {
              var linha = document.createElement('p');
              linha.textContent = mensagem;
              areaErros.appendChild(linha);
            });
            return;
          }
          oficio.textContent = resultado.oficio;
          principal.classList.add('oculto');
          confirmacao.classList.remove('oculto');
        });
    });
  });
})();
