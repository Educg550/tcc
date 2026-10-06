(function () {
  'use strict';

  function soDigitos(valor) {
    return valor.replace(/\D/g, '');
  }

  function formatarValor(valor) {
    var digitos = soDigitos(valor);
    if (!digitos) { return ''; }
    var centavos = parseInt(digitos, 10);
    var reais = Math.floor(centavos / 100);
    var resto = String(centavos % 100).padStart(2, '0');
    return 'R$ ' + reais.toLocaleString('pt-BR') + ',' + resto;
  }

  function formatarCpf(valor) {
    var d = soDigitos(valor).slice(0, 11);
    if (d.length > 9) { return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9); }
    if (d.length > 6) { return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6); }
    if (d.length > 3) { return d.slice(0, 3) + '.' + d.slice(3); }
    return d;
  }

  function formatarCep(valor) {
    var d = soDigitos(valor).slice(0, 8);
    if (d.length > 5) { return d.slice(0, 5) + '-' + d.slice(5); }
    return d;
  }

  function formatarData(valor) {
    var d = soDigitos(valor).slice(0, 8);
    if (d.length > 4) { return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4); }
    if (d.length > 2) { return d.slice(0, 2) + '/' + d.slice(2); }
    return d;
  }

  var formatadores = {
    valor: formatarValor,
    cpf: formatarCpf,
    cep: formatarCep,
    data: formatarData
  };

  document.querySelectorAll('[data-formato]').forEach(function (campo) {
    campo.addEventListener('blur', function () {
      campo.value = formatadores[campo.dataset.formato](campo.value);
    });
  });

  document.querySelectorAll('.aba').forEach(function (aba) {
    aba.addEventListener('click', function () {
      document.querySelectorAll('.aba').forEach(function (outra) {
        outra.classList.remove('ativa');
      });
      document.querySelectorAll('.painel').forEach(function (painel) {
        painel.classList.remove('ativo');
      });
      aba.classList.add('ativa');
      document.getElementById(aba.dataset.alvo).classList.add('ativo');
    });
  });

  document.querySelectorAll('form.formulario').forEach(function (form) {
    form.addEventListener('submit', function (evento) {
      evento.preventDefault();

      var dados = { aba: form.dataset.aba };
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = valor;
      });

      var caixa = form.querySelector('.erros');

      fetch('/api/solicitar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (resultado) {
          if (resultado.ok) {
            caixa.hidden = true;
            caixa.innerHTML = '';
            document.getElementById('tela-formulario').hidden = true;
            document.getElementById('oficio').textContent = resultado.oficio;
            document.getElementById('confirmacao').hidden = false;
            window.scrollTo(0, 0);
          } else {
            caixa.hidden = false;
            caixa.innerHTML = resultado.erros.map(function (erro) {
              return '<div>' + erro + '</div>';
            }).join('');
          }
        });
    });
  });
})();
