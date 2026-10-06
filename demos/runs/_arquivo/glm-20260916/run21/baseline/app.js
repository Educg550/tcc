'use strict';

const $ = (seletor, raiz = document) => raiz.querySelector(seletor);
const $$ = (seletor, raiz = document) => Array.from(raiz.querySelectorAll(seletor));

const FORMATADORES = {
  valor(texto) {
    const digitos = texto.replace(/\D/g, '');
    if (!digitos) {
      return '';
    }
    const partes = (parseInt(digitos, 10) / 100).toFixed(2).split('.');
    return 'R$ ' + partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + partes[1];
  },
  cpf(texto) {
    const d = texto.replace(/\D/g, '').slice(0, 11);
    let formatado = d.slice(0, 3);
    if (d.length > 3) {
      formatado += '.' + d.slice(3, 6);
    }
    if (d.length > 6) {
      formatado += '.' + d.slice(6, 9);
    }
    if (d.length > 9) {
      formatado += '-' + d.slice(9, 11);
    }
    return formatado;
  },
  cep(texto) {
    const d = texto.replace(/\D/g, '').slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  },
  data(texto) {
    const d = texto.replace(/\D/g, '').slice(0, 8);
    if (d.length > 4) {
      return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    }
    if (d.length > 2) {
      return d.slice(0, 2) + '/' + d.slice(2);
    }
    return d;
  }
};

function ativarAba(aba) {
  $$('.aba').forEach((botao) => {
    const ativa = botao.dataset.aba === aba;
    botao.classList.toggle('ativa', ativa);
    botao.setAttribute('aria-selected', String(ativa));
  });
  $$('.formulario').forEach((form) => {
    form.classList.toggle('oculto', form.dataset.aba !== aba);
  });
}

async function enviar(form) {
  const caixa = $('.erros', form);
  caixa.replaceChildren();
  caixa.classList.remove('visivel');
  const campos = {};
  $$('[data-campo]', form).forEach((campo) => {
    campos[campo.dataset.campo] = campo.value;
  });
  const resposta = await fetch('/api/solicitacao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/' },
    body: JSON.stringify({ aba: form.dataset.aba, campos: campos })
  });
  const dados = await resposta.();
  if (dados.erros && dados.erros.length > 0) {
    dados.erros.forEach((mensagem) => {
      const linha = document.createElement('div');
      linha.textContent = mensagem;
      caixa.appendChild(linha);
    });
    caixa.classList.add('visivel');
    caixa.focus();
    return;
  }
  $('#oficio').textContent = dados.oficio;
  $('#formulario').classList.add('oculto');
  $('#confirmacao').classList.remove('oculto');
}

$$('.aba').forEach((botao) => {
  botao.addEventListener('click', () => ativarAba(botao.dataset.aba));
});

$$('[data-formato]').forEach((campo) => {
  campo.addEventListener('blur', () => {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  });
});

$$('.formulario').forEach((form) => {
  form.addEventListener('submit', (evento) => {
    evento.preventDefault();
    enviar(form);
  });
});
