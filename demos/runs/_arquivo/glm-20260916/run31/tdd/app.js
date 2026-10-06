'use strict';

const FORMATADORES = {
  valor_solicitado: formatarValor,
  cpf: formatarCpf,
  cep: formatarCep,
  data_nascimento: formatarData,
};

function apenasDigitos(texto) {
  return texto.replace(/\D/g, '');
}

function formatarValor(campo) {
  const digitos = apenasDigitos(campo.value);
  if (!digitos) {
    campo.value = '';
    return;
  }
  const centavos = digitos.slice(-2).padStart(2, '0');
  const reais = digitos.slice(0, -2) || '0';
  const comMilhar = reais.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  campo.value = 'R$ ' + comMilhar + ',' + centavos;
}

function formatarCpf(campo) {
  const digitos = apenasDigitos(campo.value);
  if (digitos.length === 11) {
    campo.value = digitos.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
  }
}

function formatarCep(campo) {
  const digitos = apenasDigitos(campo.value);
  if (digitos.length === 8) {
    campo.value = digitos.replace(/(\d{5})(\d{3})/, '$1-$2');
  }
}

function formatarData(campo) {
  const digitos = apenasDigitos(campo.value);
  if (digitos.length === 8) {
    campo.value = digitos.replace(/(\d{2})(\d{2})(\d{4})/, '$1/$2/$3');
  }
}

function montarAbas() {
  const abas = document.querySelectorAll('.aba');
  abas.forEach((aba) => {
    aba.addEventListener('click', () => {
      abas.forEach((outra) => outra.classList.toggle('ativa', outra === aba));
      document.querySelectorAll('.painel').forEach((painel) => {
        painel.hidden = painel.id !== aba.dataset.painel;
      });
    });
  });
}

async function enviarFormulario(formulario) {
  const parametros = new URLSearchParams(new FormData(formulario));
  const campoValor = formulario.elements['valor_solicitado'];
  if (campoValor) {
    parametros.set('valor_solicitado', apenasDigitos(campoValor.value));
  }
  const resposta = await fetch('/solicitacao', { method: 'POST', body: parametros });
  const texto = await resposta.text();
  if (resposta.ok) {
    document.getElementById('oficio').textContent = texto;
    document.getElementById('formularios').hidden = true;
    document.getElementById('confirmacao').hidden = false;
    window.scrollTo(0, 0);
    return;
  }
  const caixa = formulario.querySelector('.erros');
  caixa.textContent = texto;
  caixa.hidden = false;
}

function montarFormularios() {
  document.querySelectorAll('form.documento').forEach((formulario) => {
    formulario.addEventListener('submit', (evento) => {
      evento.preventDefault();
      enviarFormulario(formulario);
    });
    Object.keys(FORMATADORES).forEach((nome) => {
      const campo = formulario.elements[nome];
      if (campo) {
        campo.addEventListener('blur', () => FORMATADORES[nome](campo));
      }
    });
  });
}

montarAbas();
montarFormularios();
