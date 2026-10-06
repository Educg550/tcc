'use strict';

const abas = document.querySelectorAll('.aba');
const formularios = {
  alunos: document.getElementById('form-alunos'),
  docentes: document.getElementById('form-docentes'),
};

function mostraAba(abaEscolhida) {
  abas.forEach((aba) => aba.classList.toggle('ativa', aba === abaEscolhida));
  for (const [chave, formulario] of Object.entries(formularios)) {
    formulario.hidden = chave !== abaEscolhida.dataset.aba;
  }
  document.getElementById('formularios').hidden = false;
  document.getElementById('confirmacao').hidden = true;
  window.scrollTo(0, 0);
}

abas.forEach((aba) => aba.addEventListener('click', () => mostraAba(aba)));

function soDigitos(texto) {
  return texto.replace(/\D/g, '');
}

function mascaraCpf(digitos) {
  const parcial = digitos.slice(0, 11);
  if (parcial.length <= 3) return parcial;
  if (parcial.length <= 6) return parcial.replace(/(\d{3})(\d+)/, '$1.$2');
  if (parcial.length <= 9) return parcial.replace(/(\d{3})(\d{3})(\d+)/, '$1.$2.$3');
  return parcial.replace(/(\d{3})(\d{3})(\d{3})(\d+)/, '$1.$2.$3-$4');
}

function mascaraCep(digitos) {
  const parcial = digitos.slice(0, 8);
  return parcial.length > 5 ? parcial.slice(0, 5) + '-' + parcial.slice(5) : parcial;
}

function mascaraData(digitos) {
  const parcial = digitos.slice(0, 8);
  return [parcial.slice(0, 2), parcial.slice(2, 4), parcial.slice(4)].filter(Boolean).join('/');
}

function mascaraMoeda(digitos) {
  if (!digitos) return '';
  const centavos = parseInt(digitos, 10);
  const reais = String(Math.trunc(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + reais + ',' + String(centavos % 100).padStart(2, '0');
}

const mascaras = { cpf: mascaraCpf, cep: mascaraCep, data: mascaraData, moeda: mascaraMoeda };

document.querySelectorAll('[data-mascara]').forEach((campo) => {
  campo.addEventListener('blur', () => {
    campo.value = mascaras[campo.dataset.mascara](soDigitos(campo.value));
  });
});

document.querySelectorAll('.painel').forEach((formulario) => {
  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const campoValor = formulario.querySelector('[data-mascara="moeda"]');
    const digitosValor = soDigitos(campoValor.value);
    campoValor.value = digitosValor;
    const corpo = new URLSearchParams(new FormData(formulario)).toString();
    campoValor.value = mascaraMoeda(digitosValor);
    const resposta = await fetch('/solicitacao', { method: 'POST', body: corpo });
    const texto = await resposta.text();
    const aviso = formulario.querySelector('.erros');
    if (resposta.ok) {
      aviso.hidden = true;
      document.getElementById('formularios').hidden = true;
      document.getElementById('confirmacao').hidden = false;
      document.getElementById('oficio').textContent = texto;
    } else {
      aviso.textContent = texto;
      aviso.hidden = false;
    }
    window.scrollTo(0, 0);
  });
});
