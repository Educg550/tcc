'use strict';

function soDigitos(texto) {
  return texto.replace(/\D/g, '');
}

function formatarMoeda(texto) {
  const digitos = soDigitos(texto);
  if (!digitos) return '';
  const centavos = parseInt(digitos, 10);
  const reais = Math.floor(centavos / 100);
  const milhar = String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + milhar + ',' + String(centavos % 100).padStart(2, '0');
}

function mascaraCpf(texto) {
  const d = soDigitos(texto).slice(0, 11);
  let r = d.slice(0, 3);
  if (d.length > 3) r += '.' + d.slice(3, 6);
  if (d.length > 6) r += '.' + d.slice(6, 9);
  if (d.length > 9) r += '-' + d.slice(9, 11);
  return r;
}

function mascaraCep(texto) {
  const d = soDigitos(texto).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function mascaraData(texto) {
  const d = soDigitos(texto).slice(0, 8);
  let r = d.slice(0, 2);
  if (d.length > 2) r += '/' + d.slice(2, 4);
  if (d.length > 4) r += '/' + d.slice(4, 8);
  return r;
}

const MASCARAS = {
  moeda: formatarMoeda,
  cpf: mascaraCpf,
  cep: mascaraCep,
  data: mascaraData,
};

document.querySelectorAll('[data-mascara]').forEach((campo) => {
  campo.addEventListener('blur', () => {
    campo.value = MASCARAS[campo.dataset.mascara](campo.value);
  });
});

document.querySelectorAll('.aba').forEach((aba) => {
  aba.addEventListener('click', () => {
    document.querySelectorAll('.aba').forEach((outra) => {
      outra.classList.toggle('ativa', outra === aba);
    });
    document.querySelectorAll('.painel').forEach((painel) => {
      painel.hidden = painel.id !== aba.dataset.alvo;
    });
  });
});

document.querySelectorAll('form.solicitacao').forEach((form) => {
  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const dados = { aba: form.dataset.aba };
    new FormData(form).forEach((valor, chave) => {
      dados[chave] = valor.trim();
    });
    const resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.();
    if (resultado.erros) {
      const caixa = form.querySelector('.erros');
      caixa.replaceChildren(...resultado.erros.map((mensagem) => {
        const p = document.createElement('p');
        p.textContent = mensagem;
        return p;
      }));
      caixa.hidden = false;
    } else {
      document.getElementById('texto-oficio').textContent = resultado.oficio;
      document.getElementById('abas').hidden = true;
      document.getElementById('conteudo').hidden = true;
      document.getElementById('confirmacao').hidden = false;
      window.scrollTo(0, 0);
    }
  });
});
