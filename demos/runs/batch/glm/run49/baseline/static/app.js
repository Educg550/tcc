const API_URL = '/api/solicitar';

function trocarAba(aba) {
  document.querySelectorAll('.aba').forEach((el) => el.classList.remove('ativa'));
  document.querySelectorAll('.painel').forEach((el) => el.classList.remove('ativo'));
  document.querySelector(`[data-aba="${aba}"]`).classList.add('ativo');
  document.getElementById(`form-${aba}`).classList.add('ativo');
}

document.querySelectorAll('.aba').forEach((el) => {
  el.addEventListener('click', () => trocarAba(el.dataset.aba));
});

async function enviarFormulario(form) {
  const aba = form.dataset.aba;
  const dados = Object.fromEntries(new FormData(form).entries());
  dados.aba = aba;
  const resposta = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
  });
  return resposta.json();
}

document.querySelectorAll('form').forEach((form) => {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const divErros = form.querySelector('.erros');
    const resposta = await enviarFormulario(form);
    if (resposta.erros.length > 0) {
      divErros.innerHTML = resposta.erros.map((e) => `<p>${e}</p>`).join('');
      divErros.classList.add('ativo');
    } else {
      document.querySelector('main').style.display = 'none';
      document.getElementById('oficio').textContent = resposta.oficio;
      document.getElementById('confirmacao').style.display = 'block';
    }
  });
});
