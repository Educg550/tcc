'use strict';

function soDigitos(valor) {
  return valor.replace(/\D/g, '');
}

function formatarValor(valor) {
  const digitos = soDigitos(valor);
  if (!digitos) return '';
  const centavos = String(parseInt(digitos, 10)).padStart(3, '0');
  const inteiro = centavos.slice(0, -2).replace(/^0+(?=\d)/, '');
  return 'R$ ' + inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + centavos.slice(-2);
}

function formatarCpf(valor) {
  const d = soDigitos(valor).slice(0, 11);
  if (d.length <= 9) return d.replace(/(\d{3})(?=\d)/g, '$1.');
  return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
}

function formatarCep(valor) {
  const d = soDigitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(valor) {
  const d = soDigitos(valor).slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
  return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
}

const FORMATADORES = {
  valor: formatarValor,
  cpf: formatarCpf,
  cep: formatarCep,
  data_nascimento: formatarData,
};

document.querySelectorAll('[data-formato]').forEach((campo) => {
  campo.addEventListener('blur', () => {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  });
});

const abas = document.querySelectorAll('.aba');
const formularios = document.querySelectorAll('form');

abas.forEach((aba) => {
  aba.addEventListener('click', () => {
    abas.forEach((outra) => outra.classList.toggle('ativa', outra === aba));
    formularios.forEach((form) => { form.hidden = form.dataset.aba !== aba.dataset.aba; });
  });
});

formularios.forEach((form) => {
  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    form.querySelectorAll('[data-formato]').forEach((campo) => {
      campo.value = FORMATADORES[campo.dataset.formato](campo.value);
    });
    const dados = { aba: form.dataset.aba };
    new FormData(form).forEach((valor, chave) => { dados[chave] = valor; });
    const resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.();
    if (resultado.oficio !== undefined) {
      document.getElementById('formulario').hidden = true;
      document.getElementById('oficio').textContent = resultado.oficio;
      document.getElementById('confirmacao').hidden = false;
    } else {
      const caixa = form.querySelector('.erros');
      caixa.replaceChildren(...resultado.erros.map((msg) => {
        const linha = document.createElement('div');
        linha.textContent = msg;
        return linha;
      }));
      caixa.hidden = false;
    }
  });
});
