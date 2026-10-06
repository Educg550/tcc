'use strict';

function digitos(valor) {
  return valor.replace(/\D/g, '');
}

function formatarMoeda(campo) {
  let d = digitos(campo.value);
  if (!d) {
    campo.value = '';
    return;
  }
  d = d.replace(/^0+/, '');
  if (!d) {
    campo.value = 'R$ 0,00';
    return;
  }
  if (d.length <= 2) {
    campo.value = 'R$ 0,' + d.padStart(2, '0');
    return;
  }
  const centavos = d.slice(-2);
  const reais = d.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  campo.value = 'R$ ' + reais + ',' + centavos;
}

function formatarCpf(campo) {
  const d = digitos(campo.value).slice(0, 11);
  let valor = d.slice(0, 3);
  if (d.length > 3) valor += '.' + d.slice(3, 6);
  if (d.length > 6) valor += '.' + d.slice(6, 9);
  if (d.length > 9) valor += '-' + d.slice(9);
  campo.value = valor;
}

function formatarCep(campo) {
  const d = digitos(campo.value).slice(0, 8);
  campo.value = d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(campo) {
  const d = digitos(campo.value).slice(0, 8);
  let valor = d.slice(0, 2);
  if (d.length > 2) valor += '/' + d.slice(2, 4);
  if (d.length > 4) valor += '/' + d.slice(4, 8);
  campo.value = valor;
}

const FORMATADORES = { moeda: formatarMoeda, cpf: formatarCpf, cep: formatarCep, data: formatarData };

document.querySelectorAll('[data-formato]').forEach(campo => {
  campo.addEventListener('blur', () => FORMATADORES[campo.dataset.formato](campo));
});

document.querySelectorAll('.aba').forEach(aba => {
  aba.addEventListener('click', () => {
    document.querySelectorAll('.aba').forEach(outra => {
      const ativa = outra === aba;
      outra.classList.toggle('ativa', ativa);
      outra.setAttribute('aria-selected', ativa ? 'true' : 'false');
    });
    document.querySelectorAll('.painel').forEach(painel => painel.classList.add('oculto'));
    document.getElementById('painel-' + aba.dataset.aba).classList.remove('oculto');
  });
});

document.querySelectorAll('form.solicitacao').forEach(form => {
  form.addEventListener('submit', async evento => {
    evento.preventDefault();
    form.querySelectorAll('[data-formato]').forEach(campo => FORMATADORES[campo.dataset.formato](campo));
    const corpo = Object.fromEntries(new FormData(form).entries());
    corpo.tipo = form.dataset.tipo;
    const resposta = await fetch('/api/solicitar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(corpo)
    });
    const resultado = await resposta.();
    if (resultado.ok) {
      document.getElementById('formulario').classList.add('oculto');
      document.getElementById('oficio').textContent = resultado.oficio;
      document.getElementById('confirmacao').classList.remove('oculto');
      return;
    }
    const caixa = form.querySelector('.erros');
    caixa.replaceChildren(...resultado.erros.map(mensagem => {
      const p = document.createElement('p');
      p.textContent = mensagem;
      return p;
    }));
    caixa.classList.remove('oculto');
  });
});
