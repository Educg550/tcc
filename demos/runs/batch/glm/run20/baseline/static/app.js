// Abas: alternar sem perder o que foi digitado
const botoes = document.querySelectorAll('.aba');
botoes.forEach((b) => {
  b.addEventListener('click', () => {
    botoes.forEach((x) => x.classList.remove('ativa'));
    b.classList.add('ativa');
    document.querySelectorAll('.painel').forEach((p) => (p.hidden = true));
    document.getElementById('aba-' + b.dataset.aba).hidden = false;
  });
});

// Máscaras aplicadas ao sair do campo (blur)
function soDigitos(v) {
  return v.replace(/\D/g, '');
}

function moeda(v) {
  const c = soDigitos(v);
  if (!c) return '';
  const reais = Math.floor(c / 100);
  const cent = c % 100;
  return 'R$ ' + String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + String(cent).padStart(2, '0');
}

function cpf(v) {
  const d = soDigitos(v).slice(0, 11);
  return d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

function cep(v) {
  const d = soDigitos(v).slice(0, 8);
  if (d.length > 5) return d.slice(0, 5) + '-' + d.slice(5);
  return d;
}

function data(v) {
  const d = soDigitos(v).slice(0, 8);
  if (d.length > 4) return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  if (d.length > 2) return d.slice(0, 2) + '/' + d.slice(2);
  return d;
}

document.querySelectorAll('[data-moeda]').forEach((el) => (el.onblur = () => (el.value = moeda(el.value))));
document.querySelectorAll('[data-cpf]').forEach((el) => (el.onblur = () => (el.value = cpf(el.value))));
document.querySelectorAll('[data-cep]').forEach((el) => (el.onblur = () => (el.value = cep(el.value))));
document.querySelectorAll('[data-data]').forEach((el) => (el.onblur = () => (el.value = data(el.value))));

// Envio
async function enviar(form) {
  const dados = Object.fromEntries(new FormData(form).entries());
  dados.tipo = form.dataset.tipo;
  const resp = await fetch('/api/solicitacao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
  });
  return resp.json();
}

document.querySelectorAll('form').forEach((form) => {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const ul = form.parentElement.querySelector('.erros');
    const r = await enviar(form);
    if (r.ok) {
      document.querySelector('main').hidden = true;
      document.getElementById('confirmacao').hidden = false;
      document.getElementById('oficio').textContent = r.oficio;
    } else {
      ul.hidden = false;
      ul.innerHTML = '';
      r.erros.forEach((msg) => {
        const li = document.createElement('li');
        li.textContent = msg;
        ul.appendChild(li);
      });
      ul.scrollIntoView({ block: 'nearest' });
    }
  });
});
