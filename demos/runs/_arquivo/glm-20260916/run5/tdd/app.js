function soDigitos(valor) {
  return valor.replace(/\D/g, '');
}

function formatarMoeda(campo) {
  var digitos = soDigitos(campo.value);
  if (!digitos) {
    campo.value = '';
    return;
  }
  digitos = digitos.replace(/^0+(?=\d)/, '');
  while (digitos.length < 3) {
    digitos = '0' + digitos;
  }
  var inteiros = digitos.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  campo.value = 'R$ ' + inteiros + ',' + digitos.slice(-2);
}

function formatarCpf(campo) {
  var d = soDigitos(campo.value).slice(0, 11);
  if (d.length > 9) {
    campo.value = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  } else if (d.length > 6) {
    campo.value = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
  } else if (d.length > 3) {
    campo.value = d.slice(0, 3) + '.' + d.slice(3);
  } else {
    campo.value = d;
  }
}

function formatarCep(campo) {
  var d = soDigitos(campo.value).slice(0, 8);
  campo.value = d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(campo) {
  var d = soDigitos(campo.value).slice(0, 8);
  if (d.length > 4) {
    campo.value = d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  } else if (d.length > 2) {
    campo.value = d.slice(0, 2) + '/' + d.slice(2);
  } else {
    campo.value = d;
  }
}

var FORMATADORES = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData
};

document.querySelectorAll('[data-formato]').forEach(function (campo) {
  campo.addEventListener('blur', function () {
    FORMATADORES[campo.getAttribute('data-formato')](campo);
  });
});

document.querySelectorAll('.aba').forEach(function (aba) {
  aba.addEventListener('click', function () {
    document.querySelectorAll('.aba').forEach(function (outra) {
      outra.classList.toggle('ativa', outra === aba);
    });
    document.querySelectorAll('.formulario').forEach(function (form) {
      form.hidden = form.id !== aba.getAttribute('data-alvo');
    });
  });
});

document.querySelectorAll('.formulario').forEach(function (form) {
  form.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    var dados = { aba: form.getAttribute('data-aba') };
    form.querySelectorAll('[name]').forEach(function (campo) {
      dados[campo.name] = campo.value;
    });
    var resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados)
    });
    var corpo = await resposta.();
    if (corpo.errors) {
      var caixa = form.querySelector('.erros');
      caixa.innerHTML = '';
      corpo.errors.forEach(function (mensagem) {
        var paragrafo = document.createElement('p');
        paragrafo.textContent = mensagem;
        caixa.appendChild(paragrafo);
      });
      return;
    }
    document.getElementById('formularios').hidden = true;
    document.getElementById('confirmacao').hidden = false;
    document.querySelector('#confirmacao .oficio').textContent = corpo.oficio;
  });
});
