function mascararValor(texto) {
  const digitos = texto.replace(/\D/g, '').replace(/^0+(?=\d)/, '');
  if (!digitos) return '';
  const centavos = parseInt(digitos, 10);
  const reais = Math.floor(centavos / 100);
  const cent = String(centavos % 100).padStart(2, '0');
  const milhar = String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + milhar + ',' + cent;
}

function mascararCpf(texto) {
  const d = texto.replace(/\D/g, '').slice(0, 11);
  let r = d.slice(0, 3);
  if (d.length > 3) r += '.' + d.slice(3, 6);
  if (d.length > 6) r += '.' + d.slice(6, 9);
  if (d.length > 9) r += '-' + d.slice(9, 11);
  return r;
}

function mascararCep(texto) {
  const d = texto.replace(/\D/g, '').slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function mascararData(texto) {
  const d = texto.replace(/\D/g, '').slice(0, 8);
  let r = d.slice(0, 2);
  if (d.length > 2) r += '/' + d.slice(2, 4);
  if (d.length > 4) r += '/' + d.slice(4, 8);
  return r;
}

const mascaras = {
  valor: mascararValor,
  cpf: mascararCpf,
  cep: mascararCep,
  data_nascimento: mascararData,
};

const abas = document.querySelectorAll('.aba');
const paineis = document.querySelectorAll('.painel');

for (const aba of abas) {
  aba.addEventListener('click', () => {
    for (const outra of abas) {
      const ativa = outra === aba;
      outra.classList.toggle('ativa', ativa);
      outra.setAttribute('aria-selected', ativa ? 'true' : 'false');
    }
    for (const painel of paineis) {
      painel.hidden = painel.id !== aba.dataset.alvo;
    }
  });
}

for (const form of document.querySelectorAll('form')) {
  for (const [nome, mascarar] of Object.entries(mascaras)) {
    const campo = form.elements[nome];
    if (!campo) continue;
    campo.addEventListener('blur', () => {
      if (campo.value.trim() !== '') {
        campo.value = mascarar(campo.value);
      }
    });
  }

  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const dados = { perfil: form.dataset.perfil };
    for (const [chave, valor] of new FormData(form)) {
      dados[chave] = valor;
    }
    const resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.();
    if (resultado.valido) {
      document.getElementById('abas').hidden = true;
      for (const painel of paineis) painel.hidden = true;
      document.getElementById('oficio').textContent = resultado.oficio;
      document.getElementById('confirmacao').hidden = false;
      window.scrollTo(0, 0);
    } else {
      const erros = form.querySelector('.erros');
      erros.replaceChildren();
      for (const mensagem of resultado.erros) {
        const p = document.createElement('p');
        p.textContent = mensagem;
        erros.appendChild(p);
      }
      erros.hidden = false;
    }
  });
}
