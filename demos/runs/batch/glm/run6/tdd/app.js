'use strict';

function soDigitos(texto) {
  var saida = '';
  var caracteres = texto || '';
  for (var i = 0; i < caracteres.length; i += 1) {
    var caractere = caracteres[i];
    if (caractere >= '0' && caractere <= '9') {
      saida += caractere;
    }
  }
  return saida;
}

function comMilhar(numero) {
  var grupos = [];
  while (numero.length > 3) {
    grupos.unshift(numero.slice(-3));
    numero = numero.slice(0, -3);
  }
  grupos.unshift(numero);
  return grupos.join('.');
}

var MASCARAS = {
  valor: function (bruto) {
    if (!bruto) {
      return '';
    }
    var centavos = parseInt(bruto, 10);
    return 'R$ ' + comMilhar(String(Math.floor(centavos / 100))) + ',' +
      String(centavos % 100).padStart(2, '0');
  },
  cpf: function (bruto) {
    if (bruto.length !== 11) {
      return bruto;
    }
    return bruto.slice(0, 3) + '.' + bruto.slice(3, 6) + '.' + bruto.slice(6, 9) + '-' + bruto.slice(9);
  },
  cep: function (bruto) {
    if (bruto.length !== 8) {
      return bruto;
    }
    return bruto.slice(0, 5) + '-' + bruto.slice(5);
  },
  nascimento: function (bruto) {
    if (bruto.length !== 8) {
      return bruto;
    }
    return bruto.slice(0, 2) + '/' + bruto.slice(2, 4) + '/' + bruto.slice(4);
  }
};

document.querySelectorAll('input[data-mascara]').forEach(function (campo) {
  var formatar = MASCARAS[campo.dataset.mascara];
  campo.dataset.bruto = '';
  campo.addEventListener('input', function () {
    campo.dataset.bruto = soDigitos(campo.value);
    campo.value = campo.dataset.bruto;
  });
  campo.addEventListener('focus', function () {
    campo.value = campo.dataset.bruto;
  });
  campo.addEventListener('blur', function () {
    campo.value = formatar(campo.dataset.bruto);
  });
});

var abas = document.querySelectorAll('.aba');
var formularios = document.querySelectorAll('.formulario');

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
    new FormData(formulario).forEach(function (valor, chave) {
      dados[chave] = valor;
    });
    formulario.querySelectorAll('input[data-mascara]').forEach(function (campo) {
      dados[campo.name] = campo.dataset.bruto;
    });
    var erros = formulario.querySelector('.erros');
    erros.replaceChildren();
    erros.hidden = true;
    fetch('/api/validar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ aba: formulario.dataset.aba, dados: dados })
    })
      .then(function (resposta) {
        return resposta.json();
      })
      .then(function (resultado) {
        if (resultado.valido) {
          document.getElementById('oficio').textContent = resultado.oficio;
          document.getElementById('formularios').hidden = true;
          document.getElementById('confirmacao').hidden = false;
          return;
        }
        resultado.erros.forEach(function (mensagem) {
          var linha = document.createElement('p');
          linha.textContent = mensagem;
          erros.appendChild(linha);
        });
        erros.hidden = false;
      });
  });
});
