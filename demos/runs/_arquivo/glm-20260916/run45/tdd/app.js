function apenasDigitos(texto) {
  return texto.replace(/[^0-9]/g, '');
}

function comMilhares(inteiro) {
  var resto = inteiro;
  var resultado = '';
  while (resto.length > 3) {
    resultado = '.' + resto.slice(-3) + resultado;
    resto = resto.slice(0, -3);
  }
  return resto + resultado;
}

function formatarMoeda(campo) {
  var digitos = apenasDigitos(campo.value);
  if (!digitos) {
    campo.value = '';
    return;
  }
  var completo = digitos.padStart(3, '0');
  var centavos = completo.slice(-2);
  var inteiro = comMilhares(completo.slice(0, -2).replace(/^0+(?=[0-9])/, ''));
  campo.value = 'R$ ' + inteiro + ',' + centavos;
}

function formatarCpf(campo) {
  var digitos = apenasDigitos(campo.value).slice(0, 11);
  if (digitos.length > 9) {
    campo.value = digitos.slice(0, 3) + '.' + digitos.slice(3, 6) + '.' + digitos.slice(6, 9) + '-' + digitos.slice(9);
  } else if (digitos.length > 6) {
    campo.value = digitos.slice(0, 3) + '.' + digitos.slice(3, 6) + '.' + digitos.slice(6);
  } else if (digitos.length > 3) {
    campo.value = digitos.slice(0, 3) + '.' + digitos.slice(3);
  } else {
    campo.value = digitos;
  }
}

function formatarCep(campo) {
  var digitos = apenasDigitos(campo.value).slice(0, 8);
  campo.value = digitos.length > 5 ? digitos.slice(0, 5) + '-' + digitos.slice(5) : digitos;
}

function formatarData(campo) {
  var digitos = apenasDigitos(campo.value).slice(0, 8);
  if (digitos.length > 4) {
    campo.value = digitos.slice(0, 2) + '/' + digitos.slice(2, 4) + '/' + digitos.slice(4);
  } else if (digitos.length > 2) {
    campo.value = digitos.slice(0, 2) + '/' + digitos.slice(2);
  } else {
    campo.value = digitos;
  }
}

var FORMATOS = { moeda: formatarMoeda, cpf: formatarCpf, cep: formatarCep, data: formatarData };

document.querySelectorAll('.aba').forEach(function (aba) {
  aba.addEventListener('click', function () {
    document.querySelectorAll('.aba').forEach(function (outra) {
      outra.classList.toggle('ativa', outra === aba);
    });
    document.querySelectorAll('.painel').forEach(function (painel) {
      painel.classList.toggle('ativo', painel.id === aba.dataset.painel);
    });
  });
});

document.querySelectorAll('[data-formato]').forEach(function (campo) {
  campo.addEventListener('blur', function () {
    FORMATOS[campo.dataset.formato](campo);
  });
});

document.querySelectorAll('.painel').forEach(function (formulario) {
  formulario.addEventListener('submit', function (evento) {
    evento.preventDefault();
    var dados = {};
    new FormData(formulario).forEach(function (valor, nome) {
      dados[nome] = valor;
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
        if (resultado.ok) {
          document.getElementById('formularios').hidden = true;
          document.getElementById('texto-oficio').textContent = resultado.oficio;
          document.getElementById('confirmacao').hidden = false;
        } else {
          formulario.querySelector('.erros').textContent = resultado.erros.join('\n');
        }
      });
  });
});
