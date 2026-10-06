(function () {
  'use strict';

  var MASCARAS = {
    moeda: function (valor) {
      var digitos = valor.replace(/\D/g, '');
      if (!digitos) {
        return '';
      }
      var centavos = parseInt(digitos, 10);
      var parteInteira = String(Math.floor(centavos / 100));
      var agrupado = '';
      while (parteInteira.length > 3) {
        agrupado = '.' + parteInteira.slice(-3) + agrupado;
        parteInteira = parteInteira.slice(0, -3);
      }
      return 'R$ ' + parteInteira + agrupado + ',' + String(centavos % 100).padStart(2, '0');
    },
    cpf: function (valor) {
      var digitos = valor.replace(/\D/g, '').slice(0, 11);
      var saida = digitos.slice(0, 3);
      if (digitos.length > 3) {
        saida += '.' + digitos.slice(3, 6);
      }
      if (digitos.length > 6) {
        saida += '.' + digitos.slice(6, 9);
      }
      if (digitos.length > 9) {
        saida += '-' + digitos.slice(9, 11);
      }
      return saida;
    },
    cep: function (valor) {
      var digitos = valor.replace(/\D/g, '').slice(0, 8);
      if (digitos.length > 5) {
        return digitos.slice(0, 5) + '-' + digitos.slice(5);
      }
      return digitos;
    },
    data: function (valor) {
      var digitos = valor.replace(/\D/g, '').slice(0, 8);
      var saida = digitos.slice(0, 2);
      if (digitos.length > 2) {
        saida += '/' + digitos.slice(2, 4);
      }
      if (digitos.length > 4) {
        saida += '/' + digitos.slice(4, 8);
      }
      return saida;
    }
  };

  function aplicarMascaras(form) {
    form.querySelectorAll('[data-mascara]').forEach(function (campo) {
      campo.value = MASCARAS[campo.dataset.mascara](campo.value);
    });
  }

  function configurarAbas() {
    var abas = document.querySelectorAll('.aba');
    abas.forEach(function (aba) {
      aba.addEventListener('click', function () {
        abas.forEach(function (outra) {
          outra.classList.toggle('ativa', outra === aba);
        });
        document.querySelectorAll('.painel').forEach(function (painel) {
          painel.hidden = painel.id !== 'painel-' + aba.dataset.aba;
        });
      });
    });
  }

  function mostrarErros(form, erros) {
    var caixa = form.querySelector('.erros');
    caixa.textContent = '';
    erros.forEach(function (mensagem) {
      var paragrafo = document.createElement('p');
      paragrafo.textContent = mensagem;
      caixa.appendChild(paragrafo);
    });
    caixa.hidden = false;
  }

  function limparErros(form) {
    var caixa = form.querySelector('.erros');
    caixa.hidden = true;
    caixa.textContent = '';
  }

  async function enviar(form) {
    aplicarMascaras(form);
    var corpo = { aba: form.dataset.aba };
    form.querySelectorAll('[name]').forEach(function (campo) {
      corpo[campo.name] = campo.value.trim();
    });
    var resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(corpo)
    });
    var dados = await resposta.();
    if (dados && dados.oficio) {
      document.getElementById('visao-formulario').hidden = true;
      document.getElementById('oficio').textContent = dados.oficio;
      document.getElementById('visao-confirmacao').hidden = false;
      window.scrollTo(0, 0);
    } else if (dados && dados.erros) {
      mostrarErros(form, dados.erros);
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    configurarAbas();
    document.querySelectorAll('form[data-aba]').forEach(function (form) {
      form.querySelectorAll('[data-mascara]').forEach(function (campo) {
        campo.addEventListener('blur', function () {
          campo.value = MASCARAS[campo.dataset.mascara](campo.value);
        });
      });
      form.addEventListener('submit', function (evento) {
        evento.preventDefault();
        limparErros(form);
        enviar(form);
      });
    });
  });
})();
