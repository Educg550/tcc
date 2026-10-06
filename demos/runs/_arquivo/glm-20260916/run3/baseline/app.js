function soDigitos(valor) {
  return valor.replace(/\D/g, '');
}

function formatarMoeda(valor) {
  var digitos = soDigitos(valor);
  if (!digitos) {
    return '';
  }
  var centavos = parseInt(digitos, 10);
  var inteiro = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + inteiro + ',' + String(centavos % 100).padStart(2, '0');
}

function formatarCpf(valor) {
  var d = soDigitos(valor).slice(0, 11);
  if (d.length <= 3) {
    return d;
  }
  if (d.length <= 6) {
    return d.slice(0, 3) + '.' + d.slice(3);
  }
  if (d.length <= 9) {
    return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
  }
  return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
}

function formatarCep(valor) {
  var d = soDigitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(valor) {
  var d = soDigitos(valor).slice(0, 8);
  if (d.length <= 2) {
    return d;
  }
  if (d.length <= 4) {
    return d.slice(0, 2) + '/' + d.slice(2);
  }
  return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
}

var formatadores = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData
};

document.querySelectorAll('[data-formato]').forEach(function (campo) {
  campo.addEventListener('input', function () {
    campo.value = formatadores[campo.dataset.formato](campo.value);
  });
});

var abas = document.querySelectorAll('.aba');
abas.forEach(function (aba) {
  aba.addEventListener('click', function () {
    abas.forEach(function (outra) {
      outra.classList.toggle('ativa', outra === aba);
    });
    document.querySelectorAll('.form').forEach(function (form) {
      form.hidden = form.dataset.form !== aba.dataset.aba;
    });
  });
});

document.querySelectorAll('.form').forEach(function (form) {
  form.addEventListener('submit', function (evento) {
    evento.preventDefault();
    enviar(form);
  });
});

async function enviar(form) {
  var aviso = form.querySelector('.erros');
  aviso.textContent = '';
  aviso.hidden = true;
  var campos = {};
  form.querySelectorAll('[name]').forEach(function (campo) {
    campos[campo.name] = campo.value;
  });
  var resposta = await fetch('/api/solicitacao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/' },
    body: JSON.stringify({ formulario: form.dataset.form, campos: campos })
  });
  var resultado = await resposta.();
  if (resultado.ok) {
    document.getElementById('formulario-view').hidden = true;
    document.getElementById('oficio').textContent = resultado.oficio;
    document.getElementById('confirmacao-view').hidden = false;
    window.scrollTo(0, 0);
    return;
  }
  resultado.erros.forEach(function (mensagem) {
    var linha = document.createElement('p');
    linha.textContent = mensagem;
    aviso.appendChild(linha);
  });
  aviso.hidden = false;
}
