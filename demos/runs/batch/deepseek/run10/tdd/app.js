const abas = document.querySelectorAll('.aba');
const formularios = document.querySelectorAll('.aba-conteudo');

abas.forEach((aba) => {
  aba.addEventListener('click', () => {
    abas.forEach((a) => a.classList.toggle('ativa', a === aba));
    formularios.forEach((f) =>
      f.classList.toggle('ativa', f.dataset.aba === aba.dataset.aba)
    );
  });
});

function formatarMoeda(input) {
  const digitos = input.value.replace(/\D/g, '');
  if (!digitos) {
    return;
  }
  const centavos = digitos.padStart(3, '0');
  const inteiros = centavos.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  input.value = 'R$ ' + inteiros + ',' + centavos.slice(-2);
}

function formatarCpf(input) {
  const d = input.value.replace(/\D/g, '').slice(0, 11);
  let valor = '';
  if (d.length > 0) valor = d.slice(0, 3);
  if (d.length > 3) valor += '.' + d.slice(3, 6);
  if (d.length > 6) valor += '.' + d.slice(6, 9);
  if (d.length > 9) valor += '-' + d.slice(9, 11);
  input.value = valor;
}

function formatarCep(input) {
  const d = input.value.replace(/\D/g, '').slice(0, 8);
  input.value = d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(input) {
  const d = input.value.replace(/\D/g, '').slice(0, 8);
  let valor = '';
  if (d.length > 0) valor = d.slice(0, 2);
  if (d.length > 2) valor += '/' + d.slice(2, 4);
  if (d.length > 4) valor += '/' + d.slice(4, 8);
  input.value = valor;
}

const formatadores = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData,
};

document.querySelectorAll('[data-mask]').forEach((input) => {
  const formatar = formatadores[input.dataset.mask];
  input.addEventListener('blur', () => formatar(input));
});

formularios.forEach((form) => {
  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const dados = { aba: form.dataset.aba };
    form.querySelectorAll('input, select, textarea').forEach((campo) => {
      dados[campo.name] = campo.value;
    });
    form.querySelectorAll('[data-mask]').forEach((campo) => {
      formatadores[campo.dataset.mask](campo);
      dados[campo.name] = campo.value;
    });

    const resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();
    const areaErros = form.querySelector('.erros');

    if (resultado.erros.length) {
      areaErros.textContent = resultado.erros.join('\n');
      return;
    }
    areaErros.textContent = '';
    document.getElementById('formulario-view').hidden = true;
    document.getElementById('oficio').textContent = resultado.oficio;
    document.getElementById('confirmacao-view').hidden = false;
  });
});
