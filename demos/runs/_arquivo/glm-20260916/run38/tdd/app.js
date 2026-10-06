'use strict';

var FORMATADORES = {
  moeda: function (valor) {
    var digitos = valor.replace(/\D/g, '');
    if (!digitos) {
      return '';
    }
    var centavos = parseInt(digitos, 10);
    var inteiro = String(Math.floor(centavos / 100)).replace(/(\d)(?=(\d{3})+$)/g, '$1.');
    return 'R$ ' + inteiro + ',' + String(centavos % 100).padStart(2, '0');
  },
  cpf: function (valor) {
    var digitos = valor.replace(/\D/g, '').slice(0, 11);
    return digitos
      .replace(/^(\d{3})(\d)/, '$1.$2')
      .replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
      .replace(/\.(\d{3})(\d{1,2})$/, '.$1-$2');
  },
  cep: function (valor) {
    var digitos = valor.replace(/\D/g, '').slice(0, 8);
    return digitos.length > 5 ? digitos.slice(0, 5) + '-' + digitos.slice(5) : digitos;
  },
  data: function (valor) {
    var digitos = valor.replace(/\D/g, '').slice(0, 8);
    var formatado = digitos.slice(0, 2);
    if (digitos.length > 2) {
      formatado += '/' + digitos.slice(2, 4);
    }
    if (digitos.length > 4) {
      formatado += '/' + digitos.slice(4, 8);
    }
    return formatado;
  }
};

document.querySelectorAll('.aba').forEach(function (aba) {
  aba.addEventListener('click', function () {
    document.querySelectorAll('.aba').forEach(function (outra) {
      var ativa = outra === aba;
      outra.classList.toggle('ativa', ativa);
      outra.setAttribute('aria-selected', ativa ? 'true' : 'false');
    });
    document.querySelectorAll('.painel').forEach(function (painel) {
      painel.hidden = painel.id !== aba.dataset.alvo;
    });
  });
});

document.querySelectorAll('form.painel').forEach(function (form) {
  form.querySelectorAll('[data-formato]').forEach(function (campo) {
    campo.addEventListener('blur', function () {
      campo.value = FORMATADORES[campo.dataset.formato](campo.value);
    });
  });

  form.addEventListener('submit', function (evento) {
    evento.preventDefault();
    var aviso = form.querySelector('.erros');
    aviso.textContent = '';
    var dados = {};
    form.querySelectorAll('[name]').forEach(function (campo) {
      dados[campo.name] = campo.value.trim();
    });
    fetch("/solicitar", {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados)
    })
      .then(function (resposta) {
        return resposta.();
      })
      .then(function (resultado) {
        if (resultado.sucesso) {
          document.getElementById('formulario').hidden = true;
          document.getElementById('oficio').textContent = resultado.oficio;
          document.getElementById('confirmacao').hidden = false;
          window.scrollTo(0, 0);
        } else {
          resultado.erros.forEach(function (mensagem) {
            var linha = document.createElement('p');
            linha.textContent = mensagem;
            aviso.appendChild(linha);
          });
        }
      });
  });
});
