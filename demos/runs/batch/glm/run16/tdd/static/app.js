function mostrarAba(aba) {
  var ativa = document.getElementById('aba-' + aba);
  var outra = document.getElementById(aba === 'alunos' ? 'aba-docentes' : 'aba-alunos');
  ativa.classList.add('ativa');
  outra.classList.remove('ativa');
  document.getElementById('form-alunos').classList.toggle('visivel', aba === 'alunos');
  document.getElementById('form-alunos').classList.toggle('oculto', aba !== 'alunos');
  document.getElementById('form-docentes').classList.toggle('visivel', aba === 'docentes');
  document.getElementById('form-docentes').classList.toggle('oculto', aba !== 'docentes');
  var erroAtivo = document.getElementById('erro-' + aba);
  var erroOutro = document.getElementById(aba === 'alunos' ? 'erro-docentes' : 'erro-alunos');
  if (erroAtivo) erroAtivo.classList.remove('oculto');
  if (erroOutro) erroOutro.classList.add('oculto');
}

function digitos(texto) {
  return (texto || '').replace(/\D/g, '');
}

function formatarMoeda(d) {
  var inteiro = d.slice(0, -2) || '0';
  var centavos = d.slice(-2).padStart(2, '0');
  var comPontos = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + comPontos + ',' + centavos;
}

function formatarData(d) {
  return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4, 8);
}

function formatarCpf(d) {
  return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9, 11);
}

function formatarCep(d) {
  return d.slice(0, 5) + '-' + d.slice(5, 8);
}

function aoPerderFoco(evento) {
  var campo = evento.target;
  var d = digitos(campo.value);
  if (!d) return;
  if (campo.classList.contains('moeda')) {
    campo.value = formatarMoeda(d);
  } else if (campo.classList.contains('data')) {
    if (d.length >= 8) campo.value = formatarData(d);
  } else if (campo.classList.contains('cpf')) {
    if (d.length >= 11) campo.value = formatarCpf(d);
  } else if (campo.classList.contains('cep')) {
    if (d.length >= 8) campo.value = formatarCep(d);
  }
}

document.addEventListener('blur', aoPerderFoco, true);

function enviarFormulario(form) {
  var dados = {};
  new FormData(form).forEach(function (valor, chave) {
    dados[chave] = valor;
  });
  var aba = form.id === 'form-alunos' ? 'alunos' : 'docentes';
  dados.aba = aba;
  var camposMoeda = form.querySelector('.moeda');
  if (camposMoeda) {
    var d = digitos(camposMoeda.value);
    dados.valor_solicitado = d || camposMoeda.value;
  }
  var campoCpf = form.querySelector('.cpf');
  if (campoCpf) {
    var dc = digitos(campoCpf.value);
    if (dc.length === 11) dados.cpf = formatarCpf(dc);
  }
  var campoCep = form.querySelector('.cep');
  if (campoCep) {
    var dp = digitos(campoCep.value);
    if (dp.length === 8) dados.cep = formatarCep(dp);
  }
  var campoData = form.querySelector('.data');
  if (campoData) {
    var dd = digitos(campoData.value);
    if (dd.length === 8) dados.data_de_nascimento = formatarData(dd);
  }
  fetch('/solicitar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados)
  }).then(function (resposta) {
    return resposta.json().then(function (corpo) {
      return { ok: resposta.ok, corpo: corpo };
    });
  }).then(function (resultado) {
    if (!resultado.ok) {
      var caixa = document.getElementById('erro-' + aba);
      caixa.textContent = resultado.corpo.erros.join('\n');
      caixa.classList.remove('oculto');
      return;
    }
    document.getElementById('form-alunos').classList.add('oculto');
    document.getElementById('form-alunos').classList.remove('visivel');
    document.getElementById('form-docentes').classList.add('oculto');
    document.getElementById('form-docentes').classList.remove('visivel');
    var errosA = document.getElementById('erro-alunos');
    if (errosA) errosA.classList.add('oculto');
    var errosD = document.getElementById('erro-docentes');
    if (errosD) errosD.classList.add('oculto');
    var abas = document.querySelector('.abas');
    if (abas) abas.classList.add('oculto');
    document.getElementById('confirmacao').classList.remove('oculto');
    document.getElementById('oficio').textContent = resultado.corpo.oficio;
  });
}

document.getElementById('form-alunos').addEventListener('submit', function (e) {
  e.preventDefault();
  enviarFormulario(e.target);
});
document.getElementById('form-docentes').addEventListener('submit', function (e) {
  e.preventDefault();
  enviarFormulario(e.target);
});
