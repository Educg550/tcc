'use strict';

const FORMATADORES = {
  valor: formatarValor,
  cpf: formatarCpf,
  cep: formatarCep,
  data_nascimento: formatarData,
};

function digitos(valor) {
  return valor.replace(/\D/g, '');
}

function formatarValor(valor) {
  const d = digitos(valor);
  if (!d) return '';
  const centavos = d.replace(/^0+/, '') || '0';
  const parteCentavos = centavos.slice(-2).padStart(2, '0');
  const parteReais = centavos.slice(0, -2) || '0';
  return 'R$ ' + parteReais.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + parteCentavos;
}

function formatarCpf(valor) {
  const d = digitos(valor).slice(0, 11);
  let saida = d.slice(0, 3);
  if (d.length > 3) saida += '.' + d.slice(3, 6);
  if (d.length > 6) saida += '.' + d.slice(6, 9);
  if (d.length > 9) saida += '-' + d.slice(9, 11);
  return saida;
}

function formatarCep(valor) {
  const d = digitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(valor) {
  const d = digitos(valor).slice(0, 8);
  let saida = d.slice(0, 2);
  if (d.length > 2) saida += '/' + d.slice(2, 4);
  if (d.length > 4) saida += '/' + d.slice(4, 8);
  return saida;
}

const abas = Array.from(document.querySelectorAll('.aba'));
const paineis = new Map();
document.querySelectorAll('.painel').forEach(painel => paineis.set(painel.id, painel));

abas.forEach(aba => {
  aba.addEventListener('click', () => {
    abas.forEach(outra => outra.classList.toggle('ativa', outra === aba));
    paineis.forEach((painel, id) => { painel.hidden = id !== aba.dataset.alvo; });
  });
});

document.querySelectorAll('.campo input[name]').forEach(campo => {
  const formatar = FORMATADORES[campo.name];
  if (formatar) {
    campo.addEventListener('blur', () => { campo.value = formatar(campo.value); });
  }
});

document.querySelectorAll('form.painel').forEach(form => {
  form.addEventListener('submit', async evento => {
    evento.preventDefault();
    Object.entries(FORMATADORES).forEach(([nome, formatar]) => {
      const campo = form.elements[nome];
      if (campo) campo.value = formatar(campo.value);
    });
    const dados = { tipo_formulario: form.dataset.tipo };
    new FormData(form).forEach((valor, chave) => { dados[chave] = valor; });
    const caixaErros = form.querySelector('.erros');
    caixaErros.textContent = '';
    caixaErros.hidden = true;
    try {
      const resposta = await fetch('/solicitar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados),
      });
      const resultado = await resposta.json();
      if (resultado.ok) {
        document.getElementById('formulario-view').hidden = true;
        document.getElementById('oficio').textContent = resultado.oficio;
        document.getElementById('confirmacao-view').hidden = false;
      } else {
        resultado.erros.forEach(mensagem => {
          const linha = document.createElement('p');
          linha.textContent = mensagem;
          caixaErros.appendChild(linha);
        });
        caixaErros.hidden = false;
      }
    } catch (erro) {
      const linha = document.createElement('p');
      linha.textContent = 'Não foi possível enviar a solicitação.';
      caixaErros.appendChild(linha);
      caixaErros.hidden = false;
    }
  });
});
