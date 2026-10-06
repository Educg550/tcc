(function () {
  'use strict';

  function apenasDigitos(texto) {
    return texto.replace(/\D/g, '');
  }

  function comSeparadores(numero) {
    var resto = String(numero);
    var saida = '';
    while (resto.length > 3) {
      saida = '.' + resto.slice(-3) + saida;
      resto = resto.slice(0, -3);
    }
    return resto + saida;
  }

  function formatarMoeda(campo) {
    var digitos = apenasDigitos(campo.value);
    if (!digitos) {
      campo.value = '';
      return;
    }
    var centavos = String(parseInt(digitos, 10));
    while (centavos.length < 3) {
      centavos = '0' + centavos;
    }
    campo.value = 'R$ ' + comSeparadores(centavos.slice(0, -2)) + ',' + centavos.slice(-2);
  }

  function formatarCpf(campo) {
    var d = apenasDigitos(campo.value).slice(0, 11);
    var texto = d;
    if (d.length > 9) {
      texto = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
    } else if (d.length > 6) {
      texto = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    } else if (d.length > 3) {
      texto = d.slice(0, 3) + '.' + d.slice(3);
    }
    campo.value = texto;
  }

  function formatarCep(campo) {
    var d = apenasDigitos(campo.value).slice(0, 8);
    campo.value = d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }

  function formatarData(campo) {
    var d = apenasDigitos(campo.value).slice(0, 8);
    if (d.length > 4) {
      campo.value = d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    } else if (d.length > 2) {
      campo.value = d.slice(0, 2) + '/' + d.slice(2);
    } else {
      campo.value = d;
    }
  }

  var formatadores = [
    ['.formato-moeda', formatarMoeda],
    ['.formato-cpf', formatarCpf],
    ['.formato-cep', formatarCep],
    ['.formato-data', formatarData]
  ];
  formatadores.forEach(function (par) {
    document.querySelectorAll(par[0]).forEach(function (campo) {
      campo.addEventListener('blur', function () {
        par[1](campo);
      });
    });
  });

  var abas = document.querySelectorAll('.aba');
  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) {
        outra.classList.remove('ativa');
      });
      aba.classList.add('ativa');
      document.querySelectorAll('.painel').forEach(function (painel) {
        painel.hidden = painel.id !== 'painel-' + aba.dataset.aba;
      });
    });
  });

  document.querySelectorAll('form[data-aba]').forEach(function (form) {
    form.addEventListener('submit', function (evento) {
      evento.preventDefault();
      var dados = { ABA: form.dataset.aba };
      form.querySelectorAll('[name]').forEach(function (campo) {
        dados[campo.name] = campo.value.trim();
      });
      fetch('/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/' },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.();
        })
        .then(function (resultado) {
          var areaDeErros = form.querySelector('.erros');
          if (resultado.erros && resultado.erros.length > 0) {
            areaDeErros.textContent = resultado.erros.join('\n');
            return;
          }
          document.getElementById('formulario').hidden = true;
          document.getElementById('oficio').textContent = resultado.oficio;
          document.getElementById('confirmacao').hidden = false;
        });
    });
  });
})();
