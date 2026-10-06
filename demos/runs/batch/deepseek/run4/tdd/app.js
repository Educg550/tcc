(function () {
  'use strict';

  var abas = Array.prototype.slice.call(document.querySelectorAll('.aba'));
  var formularios = Array.prototype.slice.call(document.querySelectorAll('.formulario'));

  function ativar(nome) {
    abas.forEach(function (aba) {
      var ativa = aba.dataset.aba === nome;
      aba.classList.toggle('ativa', ativa);
      aba.setAttribute('aria-selected', ativa ? 'true' : 'false');
    });
    formularios.forEach(function (form) {
      form.hidden = form.dataset.aba !== nome;
    });
  }

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      ativar(aba.dataset.aba);
    });
  });

  function digitos(valor) {
    var saida = '';
    valor = valor || '';
    for (var i = 0; i < valor.length; i++) {
      var caractere = valor.charAt(i);
      if (caractere >= '0' && caractere <= '9') {
        saida += caractere;
      }
    }
    return saida;
  }

  function separaMilhar(numero) {
    var texto = String(numero);
    var saida = '';
    var contador = 0;
    for (var i = texto.length - 1; i >= 0; i--) {
      saida = texto.charAt(i) + saida;
      contador += 1;
      if (contador % 3 === 0 && i > 0) {
        saida = '.' + saida;
      }
    }
    return saida;
  }

  function formatarValor(input) {
    var d = digitos(input.value);
    if (!d) { input.value = ''; return; }
    var centavos = parseInt(d, 10);
    var reais = Math.floor(centavos / 100);
    var resto = centavos % 100;
    input.value = 'R$ ' + separaMilhar(reais) + ',' + ('0' + resto).slice(-2);
  }

  function formatarCPF(input) {
    var d = digitos(input.value).slice(0, 11);
    var texto = d;
    if (d.length > 9) {
      texto = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
    } else if (d.length > 6) {
      texto = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    } else if (d.length > 3) {
      texto = d.slice(0, 3) + '.' + d.slice(3);
    }
    input.value = texto;
  }

  function formatarCEP(input) {
    var d = digitos(input.value).slice(0, 8);
    input.value = d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }

  function formatarData(input) {
    var d = digitos(input.value).slice(0, 8);
    var texto = d;
    if (d.length > 4) {
      texto = d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    } else if (d.length > 2) {
      texto = d.slice(0, 2) + '/' + d.slice(2);
    }
    input.value = texto;
  }

  var formatadores = {
    valor: formatarValor,
    cpf: formatarCPF,
    cep: formatarCEP,
    data_nascimento: formatarData
  };

  Array.prototype.slice.call(document.querySelectorAll('[data-formatar]')).forEach(function (input) {
    input.addEventListener('blur', function () {
      formatadores[input.dataset.formatar](input);
    });
  });

  function enviar(evento) {
    evento.preventDefault();
    var form = evento.currentTarget;
    var dados = {};
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = valor;
    });
    fetch('/enviar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados)
    })
      .then(function (resposta) { return resposta.json(); })
      .then(function (resultado) {
        var caixa = form.querySelector('.erros');
        if (resultado.erros && resultado.erros.length) {
          caixa.textContent = resultado.erros.join(String.fromCharCode(10));
          caixa.hidden = false;
          return;
        }
        caixa.hidden = true;
        document.getElementById('oficio').textContent = resultado.oficio;
        document.getElementById('tela-formulario').hidden = true;
        document.getElementById('confirmacao').hidden = false;
      });
  }

  formularios.forEach(function (form) {
    form.addEventListener('submit', enviar);
  });
})();
