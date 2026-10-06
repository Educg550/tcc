const FORMATADORES = {
  valor: formatarMoeda,
  cpf: formatarCPF,
  cep: formatarCEP,
  data_nascimento: formatarData,
};

function digitos(valor) {
  return valor.replace(/\D/g, '');
}

function formatarMoeda(valor) {
  const d = digitos(valor);
  if (!d) return '';
  const centavos = Number(d);
  const reais = Math.floor(centavos / 100);
  const milhar = String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + milhar + ',' + String(centavos % 100).padStart(2, '0');
}

function formatarCPF(valor) {
  const d = digitos(valor);
  return d.length === 11 ? `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}` : valor;
}

function formatarCEP(valor) {
  const d = digitos(valor);
  return d.length === 8 ? `${d.slice(0, 5)}-${d.slice(5)}` : valor;
}

function formatarData(valor) {
  const d = digitos(valor);
  return d.length === 8 ? `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}` : valor;
}

for (const [nome, formatar] of Object.entries(FORMATADORES)) {
  document.querySelectorAll(`input[name='${nome}']`).forEach((campo) => {
    campo.addEventListener('blur', () => {
      campo.value = formatar(campo.value);
    });
  });
}

const abas = document.querySelectorAll('.aba');
abas.forEach((aba) => {
  aba.addEventListener('click', () => {
    abas.forEach((outra) => {
      outra.classList.toggle('ativa', outra === aba);
      outra.setAttribute('aria-selected', outra === aba ? 'true' : 'false');
    });
    document.querySelectorAll('.painel-formulario').forEach((painel) => {
      painel.classList.toggle('oculto', painel.id !== 'painel-' + aba.dataset.alvo);
    });
  });
});

document.querySelectorAll('form').forEach((form) => {
  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    form.querySelectorAll('input').forEach((campo) => {
      const formatar = FORMATADORES[campo.name];
      if (formatar) campo.value = formatar(campo.value);
    });
    const campos = {};
    form.querySelectorAll('[name]').forEach((el) => {
      campos[el.name] = el.value;
    });
    const resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify({ tipo: form.dataset.tipo, campos: campos }),
    });
    const dados = await resposta.();
    if (dados.erros) {
      const caixa = form.querySelector('.erros');
      caixa.replaceChildren(
        ...dados.erros.map((mensagem) => {
          const p = document.createElement('p');
          p.textContent = mensagem;
          return p;
        })
      );
      caixa.classList.remove('oculto');
      caixa.scrollIntoView({ block: 'start' });
    } else {
      document.getElementById('oficio').textContent = dados.oficio;
      document.getElementById('abas').classList.add('oculto');
      document.querySelectorAll('.painel-formulario').forEach((painel) => painel.classList.add('oculto'));
      document.getElementById('confirmacao').classList.remove('oculto');
      document.getElementById('conteudo').scrollTop = 0;
    }
  });
});
