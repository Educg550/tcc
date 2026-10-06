const abas = document.querySelectorAll('.aba');
const paineis = {
  alunos: document.getElementById('alunos'),
  docentes: document.getElementById('docentes')
};

abas.forEach((aba) => {
  aba.addEventListener('click', () => {
    abas.forEach((outra) => {
      const ativa = outra === aba;
      outra.classList.toggle('ativa', ativa);
      outra.setAttribute('aria-selected', String(ativa));
      paineis[outra.getAttribute('aria-controls')].hidden = !ativa;
    });
  });
});

function digitos(campo) {
  return campo.value.replace(/\D/g, '');
}

function moeda(valor) {
  if (!valor) return '';
  const inteiro = valor.slice(0, -2) || '0';
  const centavos = valor.slice(-2).padStart(2, '0');
  const separado = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + separado + ',' + centavos;
}

function formato(nome, campo) {
  const d = digitos(campo);
  if (nome === 'valor') campo.value = moeda(d);
  if (nome === 'cpf') campo.value = d.replace(/(\d{3})(\d{3})(\d{3})(\d{0,2}).*/, '$1.$2.$3-$4');
  if (nome === 'cep') campo.value = d.replace(/(\d{5})(\d{0,3}).*/, '$1-$2');
  if (nome === 'nascimento') campo.value = d.replace(/(\d{2})(\d{2})(\d{0,4}).*/, '$1/$2/$3');
}

document.querySelectorAll('.moeda, .cpf, .cep, .data').forEach((campo) => {
  campo.addEventListener('blur', () => formato(campo.name, campo));
});

document.querySelectorAll('form.painel').forEach((form) => {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const caixa = form.querySelector('.erros');
    caixa.hidden = true;

    const dados = Object.fromEntries(new FormData(form).entries());
    dados.aba = form.id;
    if (dados.valor) dados.valor = digitos(dados.valor);

    const resposta = await fetch('/oficio', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados)
    });

    const texto = await resposta.text();
    if (resposta.ok) {
      document.getElementById('tela-formulario').hidden = true;
      const confirmacao = document.getElementById('tela-confirmacao');
      document.getElementById('oficio').textContent = texto;
      confirmacao.hidden = false;
    } else {
      caixa.textContent = texto;
      caixa.hidden = false;
    }
  });
});
