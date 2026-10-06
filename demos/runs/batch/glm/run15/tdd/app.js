function mostrarAba(alvo) {
  var alunos = document.getElementById('form-alunos');
  var docentes = document.getElementById('form-docentes');
  var bA = document.getElementById('tab-alunos');
  var bD = document.getElementById('tab-docentes');
  alunos.hidden = alvo !== 'alunos';
  docentes.hidden = alvo !== 'docentes';
  bA.classList.toggle('ativa', alvo === 'alunos');
  bD.classList.toggle('ativa', alvo === 'docentes');
}

document.getElementById('tab-alunos').addEventListener('click', function () { mostrarAba('alunos'); });
document.getElementById('tab-docentes').addEventListener('click', function () { mostrarAba('docentes'); });

function mascaraValor(campo) {
  var d = campo.value.replace(/\D/g, '').slice(0, 15);
  if (d === '') { campo.value = ''; return; }
  var centavos = parseInt(d, 10);
  var inteiro = Math.floor(centavos / 100);
  var resto = ('0' + (centavos % 100)).slice(-2);
  var parte = String(inteiro).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  campo.value = 'R$ ' + parte + ',' + resto;
}

function mascaraCpf(campo) {
  var d = campo.value.replace(/\D/g, '').slice(0, 11);
  if (d === '') { campo.value = ''; return; }
  var r = d.slice(0, 3);
  if (d.length > 3) r += '.' + d.slice(3, 6);
  if (d.length > 6) r += '.' + d.slice(6, 9);
  if (d.length > 9) r += '-' + d.slice(9, 11);
  campo.value = r;
}

function mascaraCep(campo) {
  var d = campo.value.replace(/\D/g, '').slice(0, 8);
  if (d === '') { campo.value = ''; return; }
  var r = d.slice(0, 5);
  if (d.length > 5) r += '-' + d.slice(5, 8);
  campo.value = r;
}

function mascaraData(campo) {
  var d = campo.value.replace(/\D/g, '').slice(0, 8);
  if (d === '') { campo.value = ''; return; }
  var r = d.slice(0, 2);
  if (d.length > 2) r += '/' + d.slice(2, 4);
  if (d.length > 4) r += '/' + d.slice(4, 8);
  campo.value = r;
}

function ligarMascaras(raiz) {
  raiz.querySelectorAll('[name="valor"]').forEach(function (c) { c.addEventListener('blur', function () { mascaraValor(c); }); });
  raiz.querySelectorAll('[name="cpf"]').forEach(function (c) { c.addEventListener('blur', function () { mascaraCpf(c); }); });
  raiz.querySelectorAll('[name="cep"]').forEach(function (c) { c.addEventListener('blur', function () { mascaraCep(c); }); });
  raiz.querySelectorAll('[name="nascimento"]').forEach(function (c) { c.addEventListener('blur', function () { mascaraData(c); }); });
}

ligarMascaras(document);

function enviarForm(form, url) {
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var dados = new FormData(form);
    dados.set('aba', form.getAttribute('data-aba'));
    var mensagens = document.getElementById('mensagens-' + form.getAttribute('data-aba'));
    fetch(url, { method: 'POST', body: new URLSearchParams(dados) })
      .then(function (r) { return r.json(); })
      .then(function (resp) {
        if (resp.ok) {
          document.querySelector('main').hidden = true;
          document.getElementById('oficio').textContent = resp.oficio;
          document.getElementById('confirmacao').hidden = false;
          mensagens.innerHTML = '';
        } else {
          mensagens.innerHTML = resp.erros.map(function (e) { return '<li>' + e + '</li>'; }).join('');
        }
      });
  });
}

enviarForm(document.getElementById('form-alunos'), '/solicitacao');
enviarForm(document.getElementById('form-docentes'), '/solicitacao');

document.getElementById('nova-solicitacao').addEventListener('click', function () {
  document.getElementById('confirmacao').hidden = true;
  document.querySelector('main').hidden = false;
});
