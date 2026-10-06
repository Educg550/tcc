function mostrarAba(aba) {
  document.getElementById('form-alunos').classList.toggle('oculto', aba !== 'alunos');
  document.getElementById('form-docentes').classList.toggle('oculto', aba !== 'docentes');
  document.getElementById('aba-alunos').classList.toggle('ativa', aba === 'alunos');
  document.getElementById('aba-docentes').classList.toggle('ativa', aba === 'docentes');
}

function soDigitos(texto) {
  return texto.replace(/\D/g, '');
}

function formatarValor(campo) {
  var digitos = soDigitos(campo.value);
  if (!digitos) { campo.value = ''; return; }
  var centavos = parseInt(digitos, 10);
  var reais = Math.floor(centavos / 100).toString();
  var cents = (centavos % 100).toString().padStart(2, '0');
  var partes = [];
  while (reais.length > 3) {
    partes.unshift(reais.slice(-3));
    reais = reais.slice(0, -3);
  }
  partes.unshift(reais);
  campo.value = 'R$ ' + partes.join('.') + ',' + cents;
}

function formatarCPF(campo) {
  var d = soDigitos(campo.value).slice(0, 11);
  if (d.length === 11) {
    campo.value = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  } else {
    campo.value = d;
  }
}

function formatarCEP(campo) {
  var d = soDigitos(campo.value).slice(0, 8);
  campo.value = d.length === 8 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(campo) {
  var d = soDigitos(campo.value).slice(0, 8);
  campo.value = d.length === 8 ? d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4) : d;
}

document.querySelectorAll('input[name="valor_solicitado"]').forEach(function (c) {
  c.addEventListener('blur', function () { formatarValor(c); });
});
document.querySelectorAll('input.cpf').forEach(function (c) {
  c.addEventListener('blur', function () { formatarCPF(c); });
});
document.querySelectorAll('input.cep').forEach(function (c) {
  c.addEventListener('blur', function () { formatarCEP(c); });
});
document.querySelectorAll('input.data').forEach(function (c) {
  c.addEventListener('blur', function () { formatarData(c); });
});

function enviar(evento, aba) {
  evento.preventDefault();
  var form = evento.target;
  var dados = { aba: aba };
  new FormData(form).forEach(function (valor, nome) { dados[nome] = valor; });
  fetch('/solicitar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados)
  }).then(function (r) { return r.json(); }).then(function (corpo) {
    var lista = document.getElementById('erros-' + aba);
    if (corpo.erros) {
      lista.innerHTML = '';
      corpo.erros.forEach(function (e) {
        var li = document.createElement('li');
        li.textContent = e;
        lista.appendChild(li);
      });
      lista.classList.remove('oculto');
    } else {
      lista.classList.add('oculto');
      document.getElementById('oficio').textContent = corpo.oficio;
      document.getElementById('form-alunos').classList.add('oculto');
      document.getElementById('form-docentes').classList.add('oculto');
      document.getElementById('abas').classList.add('oculto');
      document.getElementById('confirmacao').classList.remove('oculto');
    }
  });
  return false;
}
