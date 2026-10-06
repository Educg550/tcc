document.addEventListener('DOMContentLoaded', function() {
// Referências às abas
var abaAlunos = document.getElementById('aba-alunos');
var abaDocentes = document.getElementById('aba-docentes');
var btnAlunos = document.getElementById('btn-alunos');
var btnDocentes = document.getElementById('btn-docentes');

// Elementos de erro
var errosAlunos = document.getElementById('erros-alunos');
var errosDocentes = document.getElementById('erros-docentes');

// Confirmação
var confirmacao = document.getElementById('confirmacao');
var formularios = document.getElementById('formularios');
var abaNav = document.getElementById('abaNav');
var oficio = document.getElementById('oficio');

// Navegação entre abas
function mostrarAba(aba) {
if (aba === 'alunos') {
abaAlunos.classList.remove('oculto');
abaDocentes.classList.add('oculto');
btnAlunos.classList.add('ativa');
btnDocentes.classList.remove('ativa');
} else {
abaDocentes.classList.remove('oculto');
abaAlunos.classList.add('oculto');
btnDocentes.classList.add('ativa');
btnAlunos.classList.remove('ativa');
}
}

btnAlunos.addEventListener('click', function() { mostrarAba('alunos'); });
btnDocentes.addEventListener('click', function() { mostrarAba('docentes'); });

// Máscaras de formatação
function formatarMoeda(valor) {
var digitos = valor.replace(/\D/g, '');
if (digitos === '') return '';
digitos = digitos.replace(/^0+/, '');
if (digitos === '') return 'R$ 0,00';
while (digitos.length < 3) { digitos = '0' + digitos; }
var centavos = digitos.slice(-2);
var parte = digits.slice(0, -2) || '0';
var partes = [];
while (parte.length > 3) {
partes.unshift(parte.slice(-3));
parte = parte.slice(0, -3);
}
partes.unshift(parte);
var inteiro = partes.join('.');
return 'R$ ' + inteiro + ',' + centavos;
}

function formatarCPF(valor) {
var digitos = valor.replace(/\D/g, '').slice(0, 11);
return digitos.replace(/(\d{3})(\d)/, '$1.$2')
.replace(/(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
.replace(/\.(\d{3})(\d{1,2})$/, '.$1-$2');
}

function formatarCEP(valor) {
var digitos = valor.replace(/\D/g, '').slice(0, 8);
if (digitos.length > 5) {
return digitos.slice(0, 5) + '-' + digitos.slice(5);
}
return digitos;
}

function formatarData(valor) {
var digitos = valor.replace(/\D/g, '').slice(0, 8);
if (digitos.length > 4) {
return digitos.slice(0, 2) + '/' + digitos.slice(2, 4) + '/' + digitos.slice(4);
}
if (digitos.length > 2) {
return digitos.slice(0, 2) + '/' + digitos.slice(2);
}
return digitos;
}

// Aplicar máscaras ao sair do campo
var camposMascarados = document.querySelectorAll('input[data-mascara]');
camposMascarados.forEach(function(campo) {
campo.addEventListener('blur', function() {
var tipo = this.getAttribute('data-mascara');
if (tipo === 'moeda') {
this.value = formatarMoeda(this.value);
} else if (tipo === 'cpf') {
this.value = formatarCPF(this.value);
} else if (tipo === 'cep') {
this.value = formatarCEP(this.value);
} else if (tipo === 'data') {
this.value = formatarData(this.value);
}
});
});

// Coletar dados de um formulário
function coletarDados(form) {
var dados = {};
var campos = form.querySelectorAll('input[name], select[name], textarea[name]');
campos.forEach(function(campo) {
dados[campo.name] = campo.value.trim();
});
return dados;
}

// Mostrar erros em uma lista
function mostrarErros(elemento, mensagens) {
elemento.innerHTML = '';
if (mensagens.length === 0) {
elemento.classList.remove('visivel');
return;
}
var ul = document.createElement('ul');
mensagens.forEach(function(msg) {
var li = document.createElement('li');
li.textContent = msg;
ul.appendChild(li);
});
elemento.appendChild(ul);
elemento.classList.add('visivel');
}

// Enviar para o backend
function enviarSolicitacao(dados, aba, form) {
var errosEl = aba === 'alunos' ? errosAlunos : errosDocentes;
var body = JSON.stringify(dados);

fetch('/api/solicitacao/' + aba, {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: body
})
.then(function(resposta) { return resposta.json(); })
.then(function(resultado) {
if (resultado.ok) {
formularios.classList.add('oculto');
abaNav.classList.add('oculto');
confirmacao.classList.remove('oculto');
oficio.textContent = resultado.oficio;
} else {
mostrarErros(errosEl, resultado.erros);
}
})
.catch(function(erro) {
mostrarErros(errosEl, ['Erro ao enviar solicitação. Tente novamente.']);
});
}

// Eventos de envio dos formulários
document.getElementById('form-alunos').addEventListener('submit', function(evento) {
evento.preventDefault();
var dados = coletarDados(this);
enviarSolicitacao(dados, 'alunos', this);
});

document.getElementById('form-docentes').addEventListener('submit', function(evento) {
evento.preventDefault();
var dados = coletarDados(this);
enviarSolicitacao(dados, 'docentes', this);
});
});
