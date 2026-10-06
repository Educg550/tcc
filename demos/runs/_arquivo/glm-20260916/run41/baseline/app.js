'use strict';

const abas = document.querySelectorAll('.aba');
const paineis = document.querySelectorAll('.painel');

abas.forEach((aba) => {
  aba.addEventListener('click', () => {
    abas.forEach((outra) => {
      const selecionada = outra === aba;
      outra.classList.toggle('ativa', selecionada);
      outra.setAttribute('aria-selected', selecionada ? 'true' : 'false');
    });
    paineis.forEach((painel) => {
      painel.classList.toggle('ativa', painel.id === aba.dataset.painel);
    });
  });
});

function separarMilhar(numero) {
  let grupo = String(numero);
  const blocos = [];
  while (grupo.length > 3) {
    blocos.unshift(grupo.slice(-3));
    grupo = grupo.slice(0, -3);
  }
  blocos.unshift(grupo);
  return blocos.join('.');
}

function formatarCampo(campo) {
  const digitos = campo.value.replace(/\D/g, '');
  const tipo = campo.dataset.formato;
  if (tipo === 'moeda' && digitos) {
    const centavos = Number(digitos);
    campo.value = 'R$ ' + separarMilhar(Math.floor(centavos / 100)) + ',' + String(centavos % 100).padStart(2, '0');
  } else if (tipo === 'cpf' && digitos.length === 11) {
    campo.value = digitos.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
  } else if (tipo === 'cep' && digitos.length === 8) {
    campo.value = digitos.replace(/(\d{5})(\d{3})/, '$1-$2');
  } else if (tipo === 'data' && digitos.length === 8) {
    campo.value = digitos.replace(/(\d{2})(\d{2})(\d{4})/, '$1/$2/$3');
  }
}

document.querySelectorAll('[data-formato]').forEach((campo) => {
  campo.addEventListener('input', () => formatarCampo(campo));
  campo.addEventListener('blur', () => formatarCampo(campo));
});

document.querySelectorAll('form.solicitacao').forEach((form) => {
  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    form.querySelectorAll('[data-formato]').forEach(formatarCampo);

    const dados = { origem: form.dataset.origem };
    form.querySelectorAll('input, select, textarea').forEach((campo) => {
      dados[campo.name] = campo.value.trim();
    });

    const resposta = await fetch('/api/solicitacoes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados)
    });
    const resultado = await resposta.();

    if (resultado.oficio) {
      document.getElementById('oficio').textContent = resultado.oficio;
      document.getElementById('formularios').classList.add('oculto');
      document.getElementById('confirmacao').classList.remove('oculto');
    } else {
      const caixa = form.querySelector('.erros');
      const linhas = (resultado.erros || []).map((mensagem) => {
        const linha = document.createElement('div');
        linha.textContent = mensagem;
        return linha;
      });
      caixa.replaceChildren(...linhas);
      caixa.classList.remove('oculto');
    }
    window.scrollTo(0, 0);
  });
});
