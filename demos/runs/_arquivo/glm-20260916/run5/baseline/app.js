(function () {
  'use strict';

  function soDigitos(texto) {
    return texto.replace(/\D/g, '');
  }

  function formatarMoeda(texto) {
    var digitos = soDigitos(texto).slice(0, 12);
    if (!digitos) {
      return '';
    }
    var centavos = parseInt(digitos, 10);
    var reais = Math.floor(centavos / 100);
    return 'R$ ' + reais.toLocaleString('pt-BR') + ',' + String(centavos % 100).padStart(2, '0');
  }

  function formatarCpf(texto) {
    var d = soDigitos(texto).slice(0, 11);
    var formatado = d.slice(0, 3);
    if (d.length > 3) {
      formatado += '.' + d.slice(3, 6);
    }
    if (d.length > 6) {
      formatado += '.' + d.slice(6, 9);
    }
    if (d.length > 9) {
      formatado += '-' + d.slice(9);
    }
    return formatado;
  }

  function formatarCep(texto) {
    var d = soDigitos(texto).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }

  function formatarData(texto) {
    var d = soDigitos(texto).slice(0, 8);
    var formatado = d.slice(0, 2);
    if (d.length > 2) {
      formatado += '/' + d.slice(2, 4);
    }
    if (d.length > 4) {
      formatado += '/' + d.slice(4);
    }
    return formatado;
  }

  function aoSair(campo, formatador) {
    campo.addEventListener('blur', function () {
      campo.value = formatador(campo.value);
    });
  }

  var abas = document.querySelectorAll('.aba');
  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) {
        var ativa = outra === aba;
        outra.classList.toggle('ativa', ativa);
        outra.setAttribute('aria-selected', ativa ? 'true' : 'false');
        document.getElementById(outra.getAttribute('aria-controls')).hidden = !ativa;
      });
    });
  });

  document.querySelectorAll('form.formulario').forEach(function (form) {
    aoSair(form.querySelector('[name="CPF (SEPARADOS POR PONTOS E TRAÇO)"]'), formatarCpf);
    aoSair(form.querySelector('[name="CEP"]'), formatarCep);
    aoSair(form.querySelector('[name="DATA DE NASCIMENTO"]'), formatarData);

    var campoValor = form.querySelector('[name="VALOR SOLICITADO (R$)"]');
    campoValor.addEventListener('input', function () {
      campoValor.value = formatarMoeda(campoValor.value);
    });
    campoValor.addEventListener('blur', function () {
      campoValor.value = formatarMoeda(campoValor.value);
    });

    form.addEventListener('submit', function (evento) {
      evento.preventDefault();
      var campos = {};
      form.querySelectorAll('[name]').forEach(function (campo) {
        campos[campo.name] = campo.value;
      });
      fetch('/api/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/' },
        body: JSON.stringify({ papel: form.dataset.papel, campos: campos })
      })
        .then(function (resposta) {
          return resposta.();
        })
        .then(function (dados) {
          if (dados.erros) {
            var caixa = form.querySelector('.erros');
            caixa.textContent = '';
            dados.erros.forEach(function (mensagem) {
              var linha = document.createElement('div');
              linha.textContent = mensagem;
              caixa.appendChild(linha);
            });
            caixa.hidden = false;
            return;
          }
          document.getElementById('formulario').hidden = true;
          document.getElementById('oficio').textContent = dados.oficio;
          document.getElementById('confirmacao').hidden = false;
          window.scrollTo(0, 0);
        });
    });
  });
})();
