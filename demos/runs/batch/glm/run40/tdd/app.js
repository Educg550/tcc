(function () {
  'use strict';

  function soDigitos(valor) {
    return valor.replace(/\D+/g, '');
  }

  function milhar(texto) {
    return texto.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  }

  function formatarValor(valor) {
    var digitos = soDigitos(valor);
    if (!digitos) {
      return '';
    }
    var centavos = parseInt(digitos, 10);
    var reais = Math.floor(centavos / 100);
    var centesimos = centavos % 100;
    return 'R$ ' + milhar(String(reais)) + ',' + ('0' + centesimos).slice(-2);
  }

  function formatarCPF(valor) {
    var d = soDigitos(valor);
    var saida = d.slice(0, 3);
    if (d.length > 3) { saida += '.' + d.slice(3, 6); }
    if (d.length > 6) { saida += '.' + d.slice(6, 9); }
    if (d.length > 9) { saida += '-' + d.slice(9, 11); }
    return saida;
  }

  function formatarCEP(valor) {
    var d = soDigitos(valor);
    var saida = d.slice(0, 5);
    if (d.length > 5) { saida += '-' + d.slice(5, 8); }
    return saida;
  }

  function formatarData(valor) {
    var d = soDigitos(valor);
    var saida = d.slice(0, 2);
    if (d.length > 2) { saida += '/' + d.slice(2, 4); }
    if (d.length > 4) { saida += '/' + d.slice(4, 8); }
    return saida;
  }

  var mascaras = {
    valor: formatarValor,
    cpf: formatarCPF,
    cep: formatarCEP,
    data: formatarData
  };

  document.querySelectorAll('[data-mascara]').forEach(function (campo) {
    campo.addEventListener('blur', function () {
      campo.value = mascaras[campo.getAttribute('data-mascara')](campo.value);
    });
  });

  var botoes = document.querySelectorAll('.aba');
  var paineis = {
    alunos: document.getElementById('painel-alunos'),
    docentes: document.getElementById('painel-docentes')
  };

  botoes.forEach(function (botao) {
    botao.addEventListener('click', function () {
      var ativa = botao.getAttribute('data-aba');
      botoes.forEach(function (item) {
        item.classList.toggle('ativa', item === botao);
      });
      Object.keys(paineis).forEach(function (aba) {
        paineis[aba].hidden = aba !== ativa;
      });
    });
  });

  document.querySelectorAll('form').forEach(function (formulario) {
    formulario.addEventListener('submit', function (evento) {
      evento.preventDefault();
      fetch('/solicitacao', {
        method: 'POST',
        body: new URLSearchParams(new FormData(formulario))
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (resultado) { exibirResposta(formulario, resultado); });
    });
  });

  function exibirResposta(formulario, resultado) {
    var caixaErros = formulario.querySelector('.erros');
    caixaErros.innerHTML = '';
    caixaErros.classList.remove('visivel');
    if (!resultado.ok) {
      resultado.erros.forEach(function (mensagem) {
        var linha = document.createElement('p');
        linha.textContent = mensagem;
        caixaErros.appendChild(linha);
      });
      caixaErros.classList.add('visivel');
      return;
    }
    document.getElementById('oficio').textContent = resultado.oficio;
    document.getElementById('formularios').hidden = true;
    document.getElementById('confirmacao').hidden = false;
  }
}());
