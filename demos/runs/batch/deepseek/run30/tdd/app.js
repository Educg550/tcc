(function () {
  'use strict';

  function soDigitos(valor) {
    return valor.replace(/[^0-9]/g, '');
  }

  function comMilhar(inteiros) {
    var saida = '';
    var contador = 0;
    for (var i = inteiros.length - 1; i >= 0; i--) {
      saida = inteiros[i] + saida;
      contador++;
      if (contador % 3 === 0 && i > 0) {
        saida = '.' + saida;
      }
    }
    return saida;
  }

  function formataMoeda(valor) {
    var digitos = soDigitos(valor).replace(/^0+/, '');
    if (digitos === '') {
      return '';
    }
    while (digitos.length < 3) {
      digitos = '0' + digitos;
    }
    var centavos = digitos.slice(-2);
    var inteiros = digitos.slice(0, -2);
    return 'R$ ' + comMilhar(inteiros) + ',' + centavos;
  }

  function formataCPF(valor) {
    var d = soDigitos(valor).slice(0, 11);
    if (d.length > 9) {
      return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
    }
    if (d.length > 6) {
      return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    }
    if (d.length > 3) {
      return d.slice(0, 3) + '.' + d.slice(3);
    }
    return d;
  }

  function formataCEP(valor) {
    var d = soDigitos(valor).slice(0, 8);
    if (d.length > 5) {
      return d.slice(0, 5) + '-' + d.slice(5);
    }
    return d;
  }

  function formataData(valor) {
    var d = soDigitos(valor).slice(0, 8);
    if (d.length > 4) {
      return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    }
    if (d.length > 2) {
      return d.slice(0, 2) + '/' + d.slice(2);
    }
    return d;
  }

  var FORMATADORES = {
    moeda: formataMoeda,
    cpf: formataCPF,
    cep: formataCEP,
    data: formataData
  };

  Array.prototype.forEach.call(
    document.querySelectorAll('[data-formato]'),
    function (campo) {
      campo.addEventListener('blur', function () {
        var formatador = FORMATADORES[campo.dataset.formato];
        if (formatador) {
          campo.value = formatador(campo.value);
        }
      });
    }
  );

  var abas = Array.prototype.slice.call(document.querySelectorAll('.aba'));
  var formularios = Array.prototype.slice.call(document.querySelectorAll('.formulario'));

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) {
        outra.classList.toggle('ativa', outra === aba);
      });
      formularios.forEach(function (formulario) {
        formulario.hidden = formulario.dataset.aba !== aba.dataset.aba;
      });
    });
  });

  formularios.forEach(function (formulario) {
    formulario.addEventListener('submit', function (evento) {
      evento.preventDefault();
      var dados = {};
      Array.prototype.forEach.call(
        formulario.querySelectorAll('input, select, textarea'),
        function (campo) {
          if (campo.name) {
            dados[campo.name] = campo.value;
          }
        }
      );
      var rota = formulario.dataset.aba === 'alunos' ? '/alunos' : '/docentes';
      fetch(rota, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (resultado) {
          var caixa = formulario.querySelector('.erros');
          if (resultado.erros) {
            caixa.textContent = resultado.erros.join('\n');
            caixa.hidden = false;
            return;
          }
          caixa.hidden = true;
          mostrarConfirmacao(resultado.oficio);
        });
    });
  });

  function mostrarConfirmacao(oficio) {
    formularios.forEach(function (formulario) { formulario.hidden = true; });
    document.querySelector('.abas').hidden = true;
    document.getElementById('oficio').textContent = oficio;
    document.getElementById('confirmacao').hidden = false;
  }
})();
