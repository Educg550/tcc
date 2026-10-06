'use strict';

function soDigitos(texto) {
  return texto.replace(/\D/g, '');
}

function comMilhar(numero) {
  return String(numero).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

var FORMATADORES = {
  valor: function (texto) {
    var digitos = soDigitos(texto);
    if (!digitos) {
      return '';
    }
    var centavos = parseInt(digitos, 10);
    return 'R$ ' + comMilhar(Math.floor(centavos / 100)) + ',' + String(centavos % 100).padStart(2, '0');
  },
  cpf: function (texto) {
    var d = soDigitos(texto).slice(0, 11);
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
  cep: function (texto) {
    var d = soDigitos(texto).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  },
  data: function (texto) {
    var d = soDigitos(texto).slice(0, 8);
    if (d.length > 4) {
      return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    }
    if (d.length > 2) {
      return d.slice(0, 2) + '/' + d.slice(2);
    }
    return d;
  }
};

document.querySelectorAll('[data-formato]').forEach(function (campo) {
  campo.addEventListener('blur', function () {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  });
});

document.querySelectorAll('.aba').forEach(function (aba) {
  aba.addEventListener('click', function () {
    document.querySelectorAll('.aba').forEach(function (outra) {
      outra.classList.toggle('ativa', outra === aba);
    });
    document.querySelectorAll('form[data-aba]').forEach(function (form) {
      form.hidden = form.dataset.aba !== aba.dataset.aba;
    });
  });
});

document.querySelectorAll('form[data-aba]').forEach(function (form) {
  form.addEventListener('submit', function (event) {
    event.preventDefault();
    form.querySelectorAll('[data-formato]').forEach(function (campo) {
      campo.value = FORMATADORES[campo.dataset.formato](campo.value);
    });
    var dados = { aba: form.dataset.aba };
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = valor;
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
        if (!resultado.ok) {
          var area = form.querySelector('.erros');
          area.textContent = '';
          resultado.erros.forEach(function (mensagem) {
            var linha = document.createElement('div');
            linha.textContent = mensagem;
            area.appendChild(linha);
          });
          area.hidden = false;
        } else {
          document.getElementById('solicitacao').hidden = true;
          document.getElementById('confirmacao').hidden = false;
          document.getElementById('oficio').textContent = resultado.oficio;
        }
      });
  });
});
