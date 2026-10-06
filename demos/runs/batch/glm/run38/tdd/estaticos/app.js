const formularios = {
  alunos: document.querySelector('#formulario-alunos'),
  docentes: document.querySelector('#formulario-docentes'),
};

const listasErros = {
  alunos: document.querySelector('#erros-alunos'),
  docentes: document.querySelector('#erros-docentes'),
};

function mostrarAba(aba) {
  for (const nome of Object.keys(formularios)) {
    const ativa = nome === aba;
    formularios[nome].hidden = !ativa;
    formularios[nome].classList.toggle('ativo', ativa);
  }
  document.querySelectorAll('.aba').forEach((botao) => {
    const ativa = botao.dataset.aba === aba;
    botao.classList.toggle('ativa', ativa);
    botao.setAttribute('aria-selected', ativa ? 'true' : 'false');
  });
}

document.querySelectorAll('.aba').forEach((botao) => {
  botao.addEventListener('click', () => mostrarAba(botao.dataset.aba));
});

function formatarMoeda(texto) {
  const digitos = (texto.match(/\d/g) || []).join('');
  if (!digitos) return '';
  const centavos = digitos.padStart(3, '0');
  const reais = centavos.slice(0, -2);
  const grupos = reais.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + grupos + ',' + centavos.slice(-2);
}

function formatarCPF(texto) {
  const d = (texto.match(/\d/g) || []).join('').slice(0, 11);
  if (!d) return '';
  return d
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/(\d{3})\.(\d{3})\.(\d{3})(\d{1,2})$/, '$1.$2.$3-$4');
}

function formatarCEP(texto) {
  const d = (texto.match(/\d/g) || []).join('').slice(0, 8);
  if (!d) return '';
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(texto) {
  const d = (texto.match(/\d/g) || []).join('').slice(0, 8);
  if (!d) return '';
  if (d.length <= 2) return d;
  if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
  return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4, 8);
}

const formatadores = {
  moeda: formatarMoeda,
  cpf: formatarCPF,
  cep: formatarCEP,
  data: formatarData,
};

document.querySelectorAll('.moeda, .cpf, .cep, .data').forEach((campo) => {
  campo.addEventListener('blur', () => {
    const formatar = formatadores[[...campo.classList].find((c) => c in formatadores)];
    campo.value = formatar(campo.value);
  });
});

function dadosDoFormulario(formulario, aba) {
  const dados = { tipo: aba };
  for (const campo of formulario.elements) {
    if (campo.name) dados[campo.name] = campo.value.trim();
  }
  return dados;
}

function mostrarErros(aba, erros) {
  const lista = listasErros[aba];
  lista.innerHTML = '';
  for (const mensagem of erros) {
    const item = document.createElement('li');
    item.textContent = mensagem;
    lista.appendChild(item);
  }
  lista.hidden = erros.length === 0;
}

const confirmacao = document.querySelector('#confirmacao');
const oficio = document.querySelector('#oficio');

for (const [aba, formulario] of Object.entries(formularios)) {
  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const resposta = await fetch('/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dadosDoFormulario(formulario, aba)),
    });
    const corpo = await resposta.json();
    if (corpo.ok) {
      for (const form of Object.values(formularios)) form.hidden = true;
      document.querySelector('.abas').hidden = true;
      oficio.textContent = corpo.oficio;
      confirmacao.hidden = false;
      return;
    }
    mostrarErros(aba, corpo.erros);
    confirmacao.hidden = true;
  });
}

document.querySelector('#nova-solicitacao').addEventListener('click', () => {
  confirmacao.hidden = true;
  document.querySelector('.abas').hidden = false;
  mostrarAba('alunos');
});
