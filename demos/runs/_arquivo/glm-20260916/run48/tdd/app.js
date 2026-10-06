'use strict';

const formatadores = {
  valor: function (campo) {
    const digitos = campo.value.replace(/\D/g, '').slice(0, 12);
    if (!digitos) {
      campo.value = '';
      return;
    }
    campo.value = 'R$ ' + (Number(digitos) / 100).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  },
  cpf: function (campo) {
    campo.value = campo.value
      .replace(/\D/g, '')
      .slice(0, 11)
      .replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, '$1.$2.$3-$4');
  },
  cep: function (campo) {
    campo.value = campo.value
      .replace(/\D/g, '')
      .slice(0, 8)
      .replace(/(\d{5})(\d{1,3})/, '$1-$2');
  },
  data: function (campo) {
    campo.value = campo.value
      .replace(/\D/g, '')
      .slice(0, 8)
      .replace(/(\d{2})(\d{2})(\d{1,4})/, '$1/$2/$3');
  },
};

document.querySelectorAll('[data-formata]').forEach(function (campo) {
  campo.addEventListener('blur', function () {
    formatadores[campo.dataset.formata](campo);
  });
});

function mostraAba(aba) {
  document.querySelectorAll('.aba').forEach(function (botao) {
    botao.classList.toggle('ativa', botao.dataset.aba === aba);
  });
  document.getElementById('form-alunos').hidden = aba !== 'alunos';
  document.getElementById('form-docentes').hidden = aba !== 'docentes';
}

document.querySelectorAll('.aba').forEach(function (botao) {
  botao.addEventListener('click', function () {
    mostraAba(botao.dataset.aba);
  });
});

document.querySelectorAll('form').forEach(function (form) {
  form.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    const dados = Object.fromEntries(new FormData(form));
    dados.aba = form.dataset.aba;
    const resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados),
    });
    const retorno = await resposta.();
    const caixa = form.querySelector('.erros');
    if (retorno.erros) {
      caixa.replaceChildren.apply(caixa, retorno.erros.map(function (mensagem) {
        const paragrafo = document.createElement('p');
        paragrafo.textContent = mensagem;
        return paragrafo;
      }));
      caixa.hidden = false;
      return;
    }
    caixa.hidden = true;
    document.getElementById('formularios').hidden = true;
    document.getElementById('oficio').textContent = retorno.oficio;
    document.getElementById('confirmacao').hidden = false;
    window.scrollTo(0, 0);
  });
});
