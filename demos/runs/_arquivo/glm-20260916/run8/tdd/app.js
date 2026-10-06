'use strict';

function apenasDigitos(texto) {
  return texto.replace(/\D/g, '');
}

function formatarMoeda(texto) {
  const digitos = apenasDigitos(texto);
  if (!digitos) return '';
  const centavos = parseInt(digitos, 10);
  const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + reais + ',' + String(centavos % 100).padStart(2, '0');
}

function formatarCpf(texto) {
  const digitos = apenasDigitos(texto).slice(0, 11);
  let formatado = digitos.slice(0, 3);
  if (digitos.length > 3) formatado += '.' + digitos.slice(3, 6);
  if (digitos.length > 6) formatado += '.' + digitos.slice(6, 9);
  if (digitos.length > 9) formatado += '-' + digitos.slice(9);
  return formatado;
}

function formatarCep(texto) {
  const digitos = apenasDigitos(texto).slice(0, 8);
  return digitos.length > 5 ? digitos.slice(0, 5) + '-' + digitos.slice(5) : digitos;
}

function formatarData(texto) {
  const digitos = apenasDigitos(texto).slice(0, 8);
  let formatado = digitos.slice(0, 2);
  if (digitos.length > 2) formatado += '/' + digitos.slice(2, 4);
  if (digitos.length > 4) formatado += '/' + digitos.slice(4, 8);
  return formatado;
}

const formatadores = {
  valor: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data_nascimento: formatarData,
};

for (const campo of document.querySelectorAll('[name]')) {
  const formatar = formatadores[campo.name];
  if (formatar) {
    campo.addEventListener('blur', () => {
      campo.value = formatar(campo.value);
    });
  }
}

const abas = document.querySelectorAll('.aba');
for (const aba of abas) {
  aba.addEventListener('click', () => {
    for (const outra of abas) {
      outra.classList.toggle('ativa', outra === aba);
    }
    document.getElementById('painel-alunos').hidden = aba.dataset.aba !== 'alunos';
    document.getElementById('painel-docentes').hidden = aba.dataset.aba !== 'docentes';
  });
}

for (const formulario of document.querySelectorAll('form')) {
  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const dados = {};
    new FormData(formulario).forEach((valor, nome) => {
      dados[nome] = valor;
    });
    const resposta = await fetch('/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados),
    });
    const conteudo = await resposta.();
    if (!conteudo.ok) {
      const erros = formulario.querySelector('.erros');
      erros.replaceChildren();
      for (const mensagem of conteudo.erros) {
        const linha = document.createElement('div');
        linha.textContent = mensagem;
        erros.appendChild(linha);
      }
      return;
    }
    document.querySelector('.abas').hidden = true;
    document.getElementById('painel-alunos').hidden = true;
    document.getElementById('painel-docentes').hidden = true;
    document.getElementById('oficio').textContent = conteudo.oficio;
    document.getElementById('confirmacao').hidden = false;
  });
}
