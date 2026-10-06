(function () {
  var abas = document.querySelectorAll('.aba');
  var formularios = document.querySelectorAll('.formulario');
  var QUEBRA = String.fromCharCode(10);

  function ativar(aba) {
    abas.forEach(function (botao) {
      botao.classList.toggle('ativa', botao === aba);
    });
    formularios.forEach(function (formulario) {
      formulario.hidden = formulario.dataset.aba !== aba.dataset.aba;
    });
  }

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () { ativar(aba); });
  });

  function agrupar(digitos) {
    var saida = '';
    var contador = 0;
    for (var i = digitos.length - 1; i >= 0; i--) {
      if (contador === 3) {
        saida = '.' + saida;
        contador = 0;
      }
      saida = digitos[i] + saida;
      contador++;
    }
    return saida;
  }

  function soDigitos(valor) {
    return valor.replace(/[^0-9]/g, '');
  }

  function formataValor(valor) {
    var digitos = soDigitos(valor);
    if (!digitos) return '';
    var centavos = parseInt(digitos, 10);
    var reais = Math.floor(centavos / 100);
    var resto = centavos % 100;
    return 'R$ ' + agrupar(String(reais)) + ',' + String(resto).padStart(2, '0');
  }

  function formataCpf(valor) {
    var d = soDigitos(valor).slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.slice(0, 3) + '.' + d.slice(3);
    if (d.length <= 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  }

  function formataCep(valor) {
    var d = soDigitos(valor).slice(0, 8);
    if (d.length <= 5) return d;
    return d.slice(0, 5) + '-' + d.slice(5);
  }

  function formataData(valor) {
    var d = soDigitos(valor).slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
    return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  }

  var formatadores = {
    valor_solicitado: formataValor,
    cpf: formataCpf,
    cep: formataCep,
    data_nascimento: formataData
  };

  Object.keys(formatadores).forEach(function (nome) {
    document.querySelectorAll('input[name=' + nome + ']').forEach(function (campo) {
      campo.addEventListener('blur', function () {
        campo.value = formatadores[nome](campo.value);
      });
    });
  });

  function coletar(formulario) {
    var dados = { aba: formulario.dataset.aba };
    formulario.querySelectorAll('input[name], select[name], textarea[name]').forEach(function (campo) {
      dados[campo.name] = campo.value;
    });
    return dados;
  }

  formularios.forEach(function (formulario) {
    formulario.addEventListener('submit', function (evento) {
      evento.preventDefault();
      fetch('/solicitar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(coletar(formulario))
      })
        .then(function (resposta) {
          return resposta.text().then(function (texto) {
            return { ok: resposta.ok, texto: texto };
          });
        })
        .then(function (resultado) {
          if (resultado.ok) {
            document.querySelector('.abas').hidden = true;
            document.querySelector('.formularios').hidden = true;
            document.querySelector('.confirmacao').hidden = false;
            document.querySelector('#oficio').textContent = resultado.texto;
          } else {
            var caixa = formulario.querySelector('.erros');
            caixa.textContent = '';
            resultado.texto.split(QUEBRA).filter(Boolean).forEach(function (linha) {
              var paragrafo = document.createElement('p');
              paragrafo.textContent = linha;
              caixa.appendChild(paragrafo);
            });
            caixa.hidden = false;
          }
        });
    });
  });
})();
