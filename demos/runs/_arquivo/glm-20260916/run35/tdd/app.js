(function () {
  'use strict';

  var PADROES = { cpf: '999.999.999-99', cep: '99999-999', data: '99/99/9999' };

  function mascarar(texto, padrao) {
    var digitos = String(texto).replace(/\D/g, '');
    var saida = '';
    var indice = 0;
    for (var posicao = 0; posicao < padrao.length; posicao += 1) {
      if (indice >= digitos.length) {
        break;
      }
      if (padrao[posicao] === '9') {
        saida += digitos[indice];
        indice += 1;
      } else {
        saida += padrao[posicao];
      }
    }
    return saida;
  }

  function moeda(texto) {
    var digitos = String(texto).replace(/\D/g, '');
    if (!digitos) {
      return '';
    }
    var centavos = parseInt(digitos, 10);
    var reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + reais + ',' + String(centavos % 100).padStart(2, '0');
  }

  document.querySelectorAll('[data-mascara]').forEach(function (campo) {
    campo.addEventListener('blur', function () {
      var tipo = campo.dataset.mascara;
      campo.value = tipo === 'moeda' ? moeda(campo.value) : mascarar(campo.value, PADROES[tipo]);
    });
  });

  document.querySelectorAll('.aba').forEach(function (aba) {
    aba.addEventListener('click', function () {
      document.querySelectorAll('.aba').forEach(function (outra) {
        outra.classList.toggle('ativa', outra === aba);
        outra.setAttribute('aria-selected', outra === aba ? 'true' : 'false');
      });
      document.querySelectorAll('.painel').forEach(function (painel) {
        painel.hidden = painel.id !== aba.dataset.alvo;
      });
    });
  });

  document.querySelectorAll('form').forEach(function (formulario) {
    formulario.addEventListener('submit', function (evento) {
      evento.preventDefault();
      var dados = { aba: formulario.dataset.aba };
      new FormData(formulario).forEach(function (valor, chave) {
        dados[chave] = valor;
      });
      fetch('/solicitar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/' },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.(); })
        .then(function (resultado) {
          var avisos = document.getElementById('erros-' + formulario.dataset.aba);
          if (!resultado.ok) {
            avisos.replaceChildren();
            resultado.erros.forEach(function (mensagem) {
              var linha = document.createElement('p');
              linha.textContent = mensagem;
              avisos.appendChild(linha);
            });
            avisos.hidden = false;
            return;
          }
          avisos.hidden = true;
          document.getElementById('formulario').hidden = true;
          document.getElementById('oficio').textContent = resultado.oficio;
          document.getElementById('confirmacao').hidden = false;
          window.scrollTo(0, 0);
        });
    });
  });
})();
