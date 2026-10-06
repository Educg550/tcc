document.querySelectorAll('.aba').forEach(function (botao) {
botao.addEventListener('click', function () {
document.querySelectorAll('.aba').forEach(function (b) {
b.classList.remove('ativa');
});
document.querySelectorAll('.formulario').forEach(function (f) {
f.classList.remove('ativo');
});
botao.classList.add('ativa');
document.getElementById('form-' + botao.dataset.aba).classList.add('ativo');
});
});

function formataValor(texto) {
var digitos = texto.replace(/\D/g, '');
if (!digitos) return '';
var centavos = parseInt(digitos, 10);
var reais = Math.floor(centavos / 100);
var resto = centavos % 100;
var parte = reais.toString();
var grupos = [];
while (parte.length > 3) {
grupos.unshift(parte.slice(-3));
parte = parte.slice(0, -3);
}
grupos.unshift(parte);
return 'R$ ' + grupos.join('.') + ',' + String(resto).padStart(2, '0');
}

function formataData(texto) {
var digitos = texto.replace(/\D/g, '').slice(0, 8);
if (digitos.length === 8) return digitos.slice(0, 2) + '/' + digitos.slice(2, 4) + '/' + digitos.slice(4, 8);
return texto;
}

function formataCpf(texto) {
var digitos = texto.replace(/\D/g, '').slice(0, 11);
if (digitos.length === 11) return digitos.slice(0, 3) + '.' + digitos.slice(3, 6) + '.' + digitos.slice(6, 9) + '-' + digitos.slice(9, 11);
return texto;
}

function formataCep(texto) {
var digitos = texto.replace(/\D/g, '').slice(0, 8);
if (digitos.length === 8) return digitos.slice(0, 5) + '-' + digitos.slice(5, 8);
return texto;
}

var formatadores = {
'VALOR SOLICITADO (R$)': formataValor,
'DATA DE NASCIMENTO': formataData,
'CPF (SEPARADOS POR PONTOS E TRAÇO)': formataCpf,
'CEP': formataCep,
};

['form-alunos', 'form-docentes'].forEach(function (id) {
document.getElementById(id).addEventListener('focusout', function (evento) {
var formatador = formatadores[evento.target.name];
if (formatador) {
evento.target.value = formatador(evento.target.value);
}
});
});

function pegaCampos(form) {
var dados = {};
form.querySelectorAll('input, select, textarea').forEach(function (campo) {
dados[campo.name] = campo.value;
});
return dados;
}

['form-alunos', 'form-docentes'].forEach(function (id) {
document.getElementById(id).addEventListener('submit', function (evento) {
evento.preventDefault();
var form = evento.target;
var tipo = id === 'form-alunos' ? 'alunos' : 'docentes';
var caixa = form.querySelector('.erros');
fetch('/solicitacao', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ tipo: tipo, campos: pegaCampos(form) }),
}).then(function (resposta) { return resposta.json(); }).then(function (corpo) {
if (corpo.erros.length) {
caixa.innerHTML = '';
corpo.erros.forEach(function (erro) {
var li = document.createElement('li');
li.textContent = erro;
caixa.appendChild(li);
});
caixa.classList.add('ativo');
return;
}
caixa.classList.remove('ativo');
document.getElementById('app').classList.add('oculto');
document.getElementById('confirmacao').classList.remove('oculto');
document.getElementById('oficio').textContent = corpo.oficio;
});
});
});

document.getElementById('voltar').addEventListener('click', function () {
document.getElementById('confirmacao').classList.add('oculto');
document.getElementById('app').classList.remove('oculto');
});
