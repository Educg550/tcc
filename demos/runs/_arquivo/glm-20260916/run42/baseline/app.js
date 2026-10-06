'use strict';

function soDigitos(valor) {
  return valor.replace(/\D/g, '');
}

function formatarMoeda(valor) {
  const digitos = soDigitos(valor);
  if (!digitos) {
    return '';
  }
  return 'R$ ' + (parseInt(digitos, 10) / 100).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

function formatarCpf(valor) {
  const d = soDigitos(valor).slice(0, 11);
  if (d.length > 9) {
    return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  }
  if (d.length > 6) {
    return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
  }
  if (d.length > 3) {
    return d.slice(0, 3) + '.' + d.slice(3);
  }
  return d;
}

function formatarCep(valor) {
  const d = soDigitos(valor).slice(0, 8);
  if (d.length > 5) {
    return d.slice(0, 5) + '-' + d.slice(5);
  }
  return d;
}

function formatarData(valor) {
  const d = soDigitos(valor).slice(0, 8);
  if (d.length > 4) {
    return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  }
  if (d.length > 2) {
    return d.slice(0, 2) + '/' + d.slice(2);
  }
  return d;
}

const FORMATADORES = [
  ['.fmt-moeda', formatarMoeda],
  ['.fmt-cpf', formatarCpf],
  ['.fmt-cep', formatarCep],
  ['.fmt-data', formatarData]
];

for (const [seletor, formatar] of FORMATADORES) {
  for (const campo of document.querySelectorAll(seletor)) {
    campo.addEventListener('input', () => {
      campo.value = formatar(campo.value);
    });
  }
}

for (const aba of document.querySelectorAll('.aba')) {
  aba.addEventListener('click', () => {
    for (const outra of document.querySelectorAll('.aba')) {
      outra.classList.toggle('ativa', outra === aba);
    }
    for (const painel of document.querySelectorAll('.painel')) {
      painel.hidden = painel.id !== aba.dataset.alvo;
    }
  });
}

for (const form of document.querySelectorAll('form')) {
  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const dados = {};
    new FormData(form).forEach((valor, nome) => {
      dados[nome] = valor;
    });
    const resposta = await fetch('/solicitacao', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/'
      },
      body: JSON.stringify({
        aba: form.dataset.aba,
        dados: dados
      })
    });
    const resultado = await resposta.();
    const caixaDeErros = form.querySelector('.erros');
    if (resultado.erros && resultado.erros.length > 0) {
      caixaDeErros.innerHTML = '';
      for (const mensagem of resultado.erros) {
        const paragrafo = document.createElement('p');
        paragrafo.textContent = mensagem;
        caixaDeErros.appendChild(paragrafo);
      }
      caixaDeErros.hidden = false;
    } else {
      document.getElementById('formularios').hidden = true;
      document.getElementById('oficio-texto').textContent = resultado.oficio;
      document.getElementById('confirmacao').hidden = false;
    }
  });
}
