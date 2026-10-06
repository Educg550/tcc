const tabAlunos = document.getElementById('tab-alunos');
const tabDocentes = document.getElementById('tab-docentes');
const formAlunos = document.getElementById('form-alunos');
const formDocentes = document.getElementById('form-docentes');
const erroAlunos = document.getElementById('erro-alunos');
const erroDocentes = document.getElementById('erro-docentes');
const confirmacao = document.getElementById('confirmacao');
const oficioEl = document.getElementById('oficio');

function mostrarAba(aba) {
  const alunos = aba === 'alunos';
  tabAlunos.classList.toggle('ativa', alunos);
  tabDocentes.classList.toggle('ativa', !alunos);
  tabAlunos.setAttribute('aria-selected', alunos);
  tabDocentes.setAttribute('aria-selected', !alunos);
  formAlunos.hidden = !alunos;
  formDocentes.hidden = alunos;
  erroAlunos.hidden = !alunos;
  erroDocentes.hidden = alunos;
}

tabAlunos.addEventListener('click', () => mostrarAba('alunos'));
tabDocentes.addEventListener('click', () => mostrarAba('docentes'));

// ===== Formatação automática =====

function digitos(v) {
  return v.replace(/\D/g, '');
}

function formatarValor(v) {
  const d = digitos(v);
  if (!d) return '';
  const n = parseInt(d, 10);
  const reais = Math.floor(n / 100);
  const centavos = String(n % 100).padStart(2, '0');
  const reaisStr = reais.toLocaleString('pt-BR');
  return 'R$ ' + reaisStr + ',' + centavos;
}

function formatarCpf(v) {
  const d = digitos(v).slice(0, 11);
  let r = d.slice(0, 3);
  if (d.length > 3) r += '.' + d.slice(3, 6);
  if (d.length > 6) r += '.' + d.slice(6, 9);
  if (d.length > 9) r += '-' + d.slice(9, 11);
  return r;
}

function formatarCep(v) {
  const d = digitos(v).slice(0, 8);
  if (d.length <= 5) return d;
  return d.slice(0, 5) + '-' + d.slice(5, 8);
}

function formatarData(v) {
  const d = digitos(v).slice(0, 8);
  let r = d.slice(0, 2);
  if (d.length > 2) r += '/' + d.slice(2, 4);
  if (d.length > 4) r += '/' + d.slice(4, 8);
  return r;
}

function ligarFormatadores(form) {
  form.querySelector('[name="valor"]').addEventListener('blur', e => {
    e.target.value = formatarValor(e.target.value);
  });
  form.querySelector('[name="cpf"]').addEventListener('blur', e => {
    e.target.value = formatarCpf(e.target.value);
  });
  form.querySelector('[name="cep"]').addEventListener('blur', e => {
    e.target.value = formatarCep(e.target.value);
  });
  form.querySelector('[name="nascimento"]').addEventListener('blur', e => {
    e.target.value = formatarData(e.target.value);
  });
}

ligarFormatadores(formAlunos);
ligarFormatadores(formDocentes);

// ===== Envio =====

async function enviar(form) {
  const aba = form.dataset.aba;
  const dados = Object.fromEntries(new FormData(form).entries());
  dados.aba = aba;
  const resp = await fetch('/api/solicitar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
  });
  const resultado = await resp.json();
  const erroEl = aba === 'alunos' ? erroAlunos : erroDocentes;
  if (!resultado.ok) {
    erroEl.innerHTML = resultado.erros.map(e => e + '<br>').join('');
    erroEl.hidden = false;
    return;
  }
  erroEl.hidden = true;
  oficioEl.textContent = resultado.oficio;
  confirmacao.hidden = false;
  formAlunos.hidden = true;
  formDocentes.hidden = true;
  tabAlunos.hidden = true;
  tabDocentes.hidden = true;
  erroAlunos.hidden = true;
  erroDocentes.hidden = true;
  window.scrollTo(0, 0);
}

formAlunos.addEventListener('submit', e => {
  e.preventDefault();
  enviar(formAlunos);
});

formDocentes.addEventListener('submit', e => {
  e.preventDefault();
  enviar(formDocentes);
});
