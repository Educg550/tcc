'use strict';

function soDigitos(valor) {
  return valor.replace(/\D/g, '');
}

function formatarMoeda(valor) {
  const d = soDigitos(valor);
  if (!d) return '';
  const t = d.padStart(3, '0');
  const inteiro = t.slice(0, -2).replace(/^0+(?=\d)/, '');
  const milhar = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + milhar + ',' + t.slice(-2);
}

function formatarCpf(valor) {
  const d = soDigitos(valor).slice(0, 11);
  if (d.length > 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  if (d.length > 6) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
  if (d.length > 3) return d.slice(0, 3) + '.' + d.slice(3);
  return d;
}

function formatarCep(valor) {
  const d = soDigitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(valor) {
  const d = soDigitos(valor).slice(0, 8);
  if (d.length > 4) return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  if (d.length > 2) return d.slice(0, 2) + '/' + d.slice(2);
  return d;
}

const FORMATADORES = {
  valor: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data_nascimento: formatarData
};

document.querySelectorAll('.aba').forEach(function (aba) {
  aba.addEventListener('click', function () {
    document.querySelectorAll('.aba').forEach(function (outra) {
      outra.classList.toggle('ativa', outra === aba);
      outra.setAttribute('aria-selected', outra === aba ? 'true' : 'false');
    });
    document.querySelectorAll('.painel').forEach(function (painel) {
      painel.hidden = painel.id !== aba.dataset.alvo;
    });
  });
});

document.querySelectorAll('input[name]').forEach(function (input) {
  const formatar = FORMATADORES[input.name];
  if (formatar) {
    input.addEventListener('blur', function () {
      input.value = formatar(input.value);
    });
  }
});

document.querySelectorAll('form.painel').forEach(function (form) {
  form.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    const dados = {};
    new FormData(form).forEach(function (valor, campo) {
      dados[campo] = valor;
    });
    const resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify({ tipo: form.dataset.tipo, dados: dados })
    });
    const saida = await resposta.();
    const caixa = form.querySelector('.erros');
    caixa.replaceChildren();
    if (saida.erros && saida.erros.length > 0) {
      saida.erros.forEach(function (mensagem) {
        const p = document.createElement('p');
        p.textContent = mensagem;
        caixa.appendChild(p);
      });
      caixa.hidden = false;
    } else {
      document.getElementById('oficio').textContent = saida.oficio;
      document.getElementById('formularios').hidden = true;
      document.getElementById('confirmacao').hidden = false;
      window.scrollTo(0, 0);
    }
  });
});
