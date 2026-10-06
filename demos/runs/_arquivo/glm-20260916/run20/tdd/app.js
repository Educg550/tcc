(function () {
  'use strict';

  var FORMATADORES = {
    valor: function (valor) {
      var digitos = valor.replace(/\D/g, '');
      if (!digitos) {
        return '';
      }
      return 'R$ ' + parseInt(digitos, 10).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
    },
    cpf: function (valor) {
      var d = valor.replace(/\D/g, '').slice(0, 11);
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
    },
    cep: function (valor) {
      var d = valor.replace(/\D/g, '').slice(0, 8);
      return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
    },
    data_nascimento: function (valor) {
      var d = valor.replace(/\D/g, '').slice(0, 8);
      if (d.length > 4) {
        return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
      }
      if (d.length > 2) {
        return d.slice(0, 2) + '/' + d.slice(2);
      }
      return d;
    }
  };

  Object.keys(FORMATADORES).forEach(function (nome) {
    Array.prototype.forEach.call(document.querySelectorAll('input[name=' + nome + ']'), function (campo) {
      campo.addEventListener('blur', function () {
        campo.value = FORMATADORES[nome](campo.value);
      });
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll('.aba'), function (aba) {
    aba.addEventListener('click', function () {
      Array.prototype.forEach.call(document.querySelectorAll('.aba'), function (outra) {
        outra.classList.toggle('ativa', outra === aba);
      });
      Array.prototype.forEach.call(document.querySelectorAll('.formulario'), function (form) {
        form.hidden = form.id !== aba.dataset.alvo;
      });
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll('form.formulario'), function (form) {
    form.addEventListener('submit', function (evento) {
      evento.preventDefault();
      var caixa = form.querySelector('.erros');
      caixa.hidden = true;
      caixa.textContent = '';
      var dados = { aba: form.dataset.aba };
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = valor;
      });
      fetch('/api/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/' },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.(); })
        .then(function (resposta) {
          if (resposta.oficio) {
            document.getElementById('oficio').textContent = resposta.oficio;
            document.getElementById('formularios').hidden = true;
            document.getElementById('confirmacao').hidden = false;
          } else {
            caixa.textContent = (resposta.erros || []).join('\n');
            caixa.hidden = false;
          }
        });
    });
  });
})();
