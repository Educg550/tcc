(function () {
  'use strict';

  var abas = document.querySelectorAll('.aba');
  var formularios = document.querySelectorAll('.formulario');
  var confirmacao = document.getElementById('confirmacao');
  var oficioEl = document.getElementById('oficio');
  var voltar = document.getElementById('voltar');

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      var alvo = aba.getAttribute('data-aba');
      abas.forEach(function (outra) {
        var ativa = outra === aba;
        outra.classList.toggle('ativa', ativa);
        outra.setAttribute('aria-selected', ativa ? 'true' : 'false');
      });
      formularios.forEach(function (form) {
        form.classList.toggle('oculta', form.getAttribute('data-tipo') !== alvo);
      });
      confirmacao.classList.add('oculta');
    });
  });

  function formatarValor(campo) {
    var digitados = campo.value.replace(/\D/g, '');
    if (!digitados) { campo.value = ''; return; }
    var inteiro = digitados.slice(0, digitados.length - 2) || '0';
    var centavos = digitados.slice(-2).padStart(2, '0');
    campo.value = 'R$ ' + inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + centavos;
  }

  function formatarData(campo) {
    var digitados = campo.value.replace(/\D/g, '').slice(0, 8);
    var partes = [];
    if (digitados.length > 0) partes.push(digitados.slice(0, 2));
    if (digitados.length > 2) partes.push(digitados.slice(2, 4));
    if (digitados.length > 4) partes.push(digitados.slice(4, 8));
    campo.value = partes.join('/');
  }

  function formatarCpf(campo) {
    var digitados = campo.value.replace(/\D/g, '').slice(0, 11);
    var formatado = digitados;
    if (digitados.length > 9) {
      formatado = digitados.slice(0, 3) + '.' + digitados.slice(3, 6) + '.' + digitados.slice(6, 9) + '-' + digitados.slice(9);
    } else if (digitados.length > 6) {
      formatado = digitados.slice(0, 3) + '.' + digitados.slice(3, 6) + '.' + digitados.slice(6);
    } else if (digitados.length > 3) {
      formatado = digitados.slice(0, 3) + '.' + digitados.slice(3);
    }
    campo.value = formatado;
  }

  function formatarCep(campo) {
    var digitados = campo.value.replace(/\D/g, '').slice(0, 8);
    campo.value = digitados.length > 5 ? digitados.slice(0, 5) + '-' + digitados.slice(5) : digitados;
  }

  var FORMATADORES = { moeda: formatarValor, data: formatarData, cpf: formatarCpf, cep: formatarCep };

  Object.keys(FORMATADORES).forEach(function (classe) {
    document.querySelectorAll('.' + classe).forEach(function (campo) {
      campo.addEventListener('blur', function () { FORMATADORES[classe](campo); });
    });
  });

  formularios.forEach(function (form) {
    form.addEventListener('submit', function (evento) {
      evento.preventDefault();
      var painel = form.querySelector('.erros');
      var dados = { tipo: form.getAttribute('data-tipo') };
      new FormData(form).forEach(function (valor, chave) { dados[chave] = String(valor).trim(); });

      fetch('/solicitar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (resultado) {
          if (resultado.erros && resultado.erros.length) {
            painel.textContent = resultado.erros.join('\n');
            painel.hidden = false;
            confirmacao.classList.add('oculta');
            form.classList.remove('oculta');
            form.scrollIntoView({ block: 'start' });
          } else {
            painel.hidden = true;
            painel.textContent = '';
            oficioEl.textContent = resultado.oficio;
            form.classList.add('oculta');
            confirmacao.classList.remove('oculta');
            window.scrollTo(0, 0);
          }
        });
    });
  });

  voltar.addEventListener('click', function () {
    confirmacao.classList.add('oculta');
    document.querySelector('.formulario:not(.oculta)') || formularios[0].classList.remove('oculta');
  });

})();
