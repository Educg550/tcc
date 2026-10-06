const abas = document.querySelectorAll('.aba');
const formularios = document.querySelectorAll('.formulario');

abas.forEach(aba => aba.addEventListener('click', () => {
  abas.forEach(outra => {
    const ativa = outra === aba;
    outra.classList.toggle('ativa', ativa);
    outra.setAttribute('aria-selected', String(ativa));
  });
  formularios.forEach(form => {
    form.hidden = form.dataset.aba !== aba.dataset.aba;
  });
}));

const mascaras = {
  moeda(valor) {
    const digitos = valor.replace(/\D/g, '');
    if (!digitos) return '';
    const centavos = Number(digitos);
    const inteiros = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+$)/g, '.');
    return 'R$ ' + inteiros + ',' + String(centavos % 100).padStart(2, '0');
  },
  cpf(valor) {
    const d = valor.replace(/\D/g, '').slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`;
    if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
    return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
  },
  cep(valor) {
    const d = valor.replace(/\D/g, '').slice(0, 8);
    return d.length <= 5 ? d : `${d.slice(0, 5)}-${d.slice(5)}`;
  },
  data(valor) {
    const d = valor.replace(/\D/g, '').slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return `${d.slice(0, 2)}/${d.slice(2)}`;
    return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
  }
};

document.querySelectorAll('[data-mascara]').forEach(campo => {
  campo.addEventListener('blur', () => {
    campo.value = mascaras[campo.dataset.mascara](campo.value);
  });
});

formularios.forEach(form => form.addEventListener('submit', async evento => {
  evento.preventDefault();
  const resposta = await fetch('/api/solicitar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ aba: form.dataset.aba, campos: Object.fromEntries(new FormData(form)) })
  });
  const dados = await resposta.json();

  const caixa = form.querySelector('.erros');
  caixa.textContent = '';
  dados.erros.forEach(mensagem => {
    const linha = document.createElement('p');
    linha.textContent = mensagem;
    caixa.appendChild(linha);
  });
  caixa.hidden = dados.erros.length === 0;
  if (dados.erros.length) return;

  document.getElementById('oficio').textContent = dados.oficio;
  document.getElementById('formularios').hidden = true;
  document.querySelector('.abas').hidden = true;
  document.getElementById('confirmacao').hidden = false;
  window.scrollTo(0, 0);
}));
