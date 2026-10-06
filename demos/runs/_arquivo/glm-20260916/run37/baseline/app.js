'use strict';

const FORMATADORES = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData
};

function soDigitos(texto) {
  return texto.replace(/\D+/g, '');
}

function formatarMoeda(digitos) {
  if (!digitos) return '';
  const centavos = parseInt(digitos, 10);
  const inteiro = Math.floor(centavos / 100).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + inteiro + ',' + String(centavos % 100).padStart(2, '0');
}

function formatarCpf(digitos) {
  digitos = digitos.slice(0, 11);
  let saida = digitos.slice(0, 3);
  if (digitos.length > 3) saida += '.' + digitos.slice(3, 6);
  if (digitos.length > 6) saida += '.' + digitos.slice(6, 9);
  if (digitos.length > 9) saida += '-' + digitos.slice(9, 11);
  return saida;
}

function formatarCep(digitos) {
  digitos = digitos.slice(0, 8);
  return digitos.length > 5 ? digitos.slice(0, 5) + '-' + digitos.slice(5) : digitos;
}

function formatarData(digitos) {
  digitos = digitos.slice(0, 8);
  let saida = digitos.slice(0, 2);
  if (digitos.length > 2) saida += '/' + digitos.slice(2, 4);
  if (digitos.length > 4) saida += '/' + digitos.slice(4, 8);
  return saida;
}

document.querySelectorAll('input[data-fmt]').forEach(function (campo) {
  campo.addEventListener('blur', function () {
    campo.value = FORMATADORES[campo.dataset.fmt](soDigitos(campo.value));
  });
});

const abas = Array.from(document.querySelectorAll('.aba'));
abas.forEach(function (aba) {
  aba.addEventListener('click', function () {
    abas.forEach(function (outra) {
      const ativa = outra === aba;
      outra.classList.toggle('ativa', ativa);
      outra.setAttribute('aria-selected', String(ativa));
      document.getElementById(outra.dataset.alvo).classList.toggle('oculto', !ativa);
    });
  });
});

function mostrarErro(caixa, mensagem) {
  const linha = document.createElement('div');
  linha.textContent = mensagem;
  caixa.appendChild(linha);
}

document.querySelectorAll('form.solicitacao').forEach(function (form) {
  form.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    const dados = { aba: form.dataset.aba };
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = valor;
    });
    const caixa = form.querySelector('.erros');
    caixa.replaceChildren();
    let resposta;
    try {
      resposta = await fetch('/api/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/' },
        body: JSON.stringify(dados)
      });
      resposta = await resposta.();
    } catch (erro) {
      mostrarErro(caixa, 'Não foi possível enviar a solicitação. Tente novamente.');
      return;
    }
    if (resposta.valido) {
      document.getElementById('formulario-view').classList.add('oculto');
      document.getElementById('oficio').textContent = resposta.oficio;
      document.getElementById('confirmacao').classList.remove('oculto');
      window.scrollTo(0, 0);
    } else {
      resposta.erros.forEach(function (mensagem) {
        mostrarErro(caixa, mensagem);
      });
    }
  });
});
