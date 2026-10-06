'use strict';

const formAlunos = document.getElementById('form-alunos');
const formDocentes = document.getElementById('form-docentes');

for (const aba of document.querySelectorAll('.aba')) {
  aba.addEventListener('click', () => {
    for (const outra of document.querySelectorAll('.aba')) {
      const ativa = outra === aba;
      outra.classList.toggle('ativa', ativa);
      outra.setAttribute('aria-selected', String(ativa));
    }
    formAlunos.hidden = aba.id !== 'aba-alunos';
    formDocentes.hidden = aba.id !== 'aba-docentes';
  });
}

function soDigitos(texto) {
  return texto.replace(/\D/g, '');
}

function formatarValor(texto) {
  const digitos = soDigitos(texto);
  if (!digitos) return '';
  const centavos = parseInt(digitos, 10);
  const reais = String(Math.trunc(centavos / 100));
  return 'R$ ' + reais.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + String(centavos % 100).padStart(2, '0');
}

function formatarCpf(texto) {
  const d = soDigitos(texto).slice(0, 11);
  if (d.length > 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  if (d.length > 6) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
  if (d.length > 3) return d.slice(0, 3) + '.' + d.slice(3);
  return d;
}

function formatarCep(texto) {
  const d = soDigitos(texto).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(texto) {
  const d = soDigitos(texto).slice(0, 8);
  if (d.length > 4) return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  if (d.length > 2) return d.slice(0, 2) + '/' + d.slice(2);
  return d;
}

const FORMATADORES = { valor: formatarValor, cpf: formatarCpf, cep: formatarCep, data: formatarData };

for (const campo of document.querySelectorAll('[data-formato]')) {
  campo.addEventListener('blur', () => {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  });
}

async function enviarSolicitacao(form, aba) {
  const dados = { aba: aba };
  for (const [campo, valor] of new FormData(form)) {
    dados[campo] = valor;
  }
  const resposta = await fetch('/api/solicitacao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/' },
    body: JSON.stringify(dados),
  });
  const resultado = await resposta.();
  const caixaErros = form.querySelector('.erros');
  if (resultado.oficio) {
    caixaErros.hidden = true;
    document.getElementById('formulario').hidden = true;
    document.getElementById('oficio').textContent = resultado.oficio;
    document.getElementById('confirmacao').hidden = false;
  } else {
    caixaErros.replaceChildren(
      ...resultado.erros.map((mensagem) => {
        const paragrafo = document.createElement('p');
        paragrafo.textContent = mensagem;
        return paragrafo;
      })
    );
    caixaErros.hidden = false;
  }
}

formAlunos.addEventListener('submit', (evento) => {
  evento.preventDefault();
  enviarSolicitacao(formAlunos, 'alunos');
});

formDocentes.addEventListener('submit', (evento) => {
  evento.preventDefault();
  enviarSolicitacao(formDocentes, 'docentes');
});
