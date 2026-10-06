// ABAS
const abas = document.querySelectorAll('.aba');
abas.forEach(a => a.addEventListener('click', () => {
abas.forEach(x => x.classList.remove('ativa'));
a.classList.add('ativa');
document.querySelectorAll('section:not(#confirmacao)').forEach(s => s.classList.remove('visivel'));
document.getElementById(a.dataset.aba).classList.add('visivel');
}));

// FORMATAÇÃO
function digitos(s) { return s.replace(/\D/g, ''); }

function fmtMoeda(s) {
s = digitos(s).replace(/^0+/, '');
if (!s) return '';
let cent = s.slice(-2).padStart(2, '0');
let int = s.slice(0, -2);
int = int.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
return 'R$ ' + int + ',' + cent;
}

function fmtCPF(s) {
s = digitos(s).slice(0, 11);
return s.length > 9 ? s.slice(0,3) + '.' + s.slice(3,6) + '.' + s.slice(6,9) + '-' + s.slice(9)
: s.length > 6 ? s.slice(0,3) + '.' + s.slice(3,6) + '.' + s.slice(6)
: s.length > 3 ? s.slice(0,3) + '.' + s.slice(3)
: s;
}

function fmtCEP(s) {
s = digitos(s).slice(0, 8);
return s.length > 5 ? s.slice(0,5) + '-' + s.slice(5) : s;
}

function fmtData(s) {
s = digitos(s).slice(0, 8);
if (s.length > 4) return s.slice(0,2) + '/' + s.slice(2,4) + '/' + s.slice(4);
if (s.length > 2) return s.slice(0,2) + '/' + s.slice(2);
return s;
}

const fmt = { moeda: fmtMoeda, cpf: fmtCPF, cep: fmtCEP, data: fmtData };
document.querySelectorAll('.moeda,.cpf,.cep,.data').forEach(el => {
el.addEventListener('blur', () => { el.value = fmt[el.classList[0]](el.value); });
});

// ENVIO
document.querySelectorAll('form[data-perfil]').forEach(form => {
form.addEventListener('submit', async ev => {
ev.preventDefault();
const errosDiv = form.querySelector('.erros');
errosDiv.hidden = true;
errosDiv.innerHTML = '';
const dados = {};
new FormData(form).forEach((v, k) => dados[k] = v);
const resp = await fetch('/api/solicitacao', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ perfil: form.dataset.perfil, dados })
});
const r = await resp.json();
if (!r.ok) {
errosDiv.innerHTML = r.erros.map(e => '<p>' + e + '</p>').join('');
errosDiv.hidden = false;
return;
}
document.querySelectorAll('section').forEach(s => { s.hidden = true; s.classList.remove('visivel'); });
document.getElementById('confirmacao').hidden = false;
document.getElementById('oficio').textContent = r.oficio;
});
});
