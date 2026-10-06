// Alternância de abas
const abas = document.querySelectorAll('.aba');
const formularios = {
  ALUNOS: document.getElementById('form-alunos'),
  DOCENTES: document.getElementById('form-docentes'),
};

function ativarAba(nome) {
  abas.forEach((aba) => aba.classList.toggle('ativa', aba.dataset.aba === nome));
  Object.entries(formularios).forEach(([chave, form]) => {
    form.classList.toggle('ativo', chave === nome);
    form.hidden = chave !== nome;
  });
}

abas.forEach((aba) => aba.addEventListener('click', () => ativarAba(aba.dataset.aba)));

// Máscaras: aplicadas ao sair do campo
function soDigitos(texto) {
  return texto.replace(/\D/g, '');
}

function formatarMoeda(digitos) {
  digitos = digitos.replace(/^0+(?=\d)/, '');
  const valor = parseInt(digitos || '0', 10);
  const centavos = (valor % 100).toString().padStart(2, '0');
  let reais = Math.floor(valor / 100).toString();
  reais = reais.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `R$ ${reais},${centavos}`;
}

function formatarCpf(d) {
  return d.length <= 3 ? d
    : d.length <= 6 ? `${d.slice(0, 3)}.${d.slice(3)}`
    : d.length <= 9 ? `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`
    : `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9, 11)}`;
}

function formatarCep(d) {
  return d.length <= 5 ? d : `${d.slice(0, 5)}-${d.slice(5, 8)}`;
}

function formatarData(d) {
  const t = d.slice(0, 8);
  if (t.length <= 2) return t;
  if (t.length <= 4) return `${t.slice(0, 2)}/${t.slice(2)}`;
  return `${t.slice(0, 2)}/${t.slice(2, 4)}/${t.slice(4)}`;
}

function aplicarMascara(campo) {
  const tipo = campo.dataset.mascara;
  const d = soDigitos(campo.value);
  let formatado = d;
  if (tipo === 'moeda') formatado = formatarMoeda(d);
  else if (tipo === 'cpf') formatado = formatarCpf(d);
  else if (tipo === 'cep') formatado = formatarCep(d);
  else if (tipo === 'data') formatado = formatarData(d);
  if (campo.value !== formatado) campo.value = formatado;
}

document.querySelectorAll('[data-mascara]').forEach((campo) => {
  campo.addEventListener('blur', () => aplicarMascara(campo));
});

// Envio
async function enviar(form, aba) {
  const dados = Object.fromEntries(new FormData(form));
  dados.aba = aba;
  const resposta = await fetch('/solicitar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
  });
  return resposta.json();
}

function exibirErros(form, erros) {
  const div = form.querySelector('.erros');
  div.innerHTML = '';
  if (erros.length) {
    const ul = document.createElement('ul');
    erros.forEach((msg) => {
      const li = document.createElement('li');
      li.textContent = msg;
      ul.appendChild(li);
    });
    div.appendChild(ul);
    div.hidden = false;
  } else {
    div.hidden = true;
  }
}

function exibirOficio(oficio) {
  document.querySelector('.abas').hidden = true;
  Object.values(formularios).forEach((f) => { f.hidden = true; f.classList.remove('ativo'); });
  document.getElementById('oficio').textContent = oficio;
  document.getElementById('confirmacao').hidden = false;
}

Object.entries(formularios).forEach(([aba, form]) => {
  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    document.querySelectorAll('[data-mascara]').forEach(aplicarMascara);
    const resultado = await enviar(form, aba);
    if (resultado.ok) {
      exibirOficio(resultado.oficio);
    } else {
      exibirErros(form, resultado.erros);
    }
  });
});
