'use strict';

const FORMATADORES = {
  valor: function (texto) {
    const digitos = texto.replace(/\D/g, '').replace(/^0+(?=\d)/, '');
    if (!digitos) return '';
    const centavos = parseInt(digitos, 10);
    const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + reais + ',' + String(centavos % 100).padStart(2, '0');
  },
  cpf: function (texto) {
    const d = texto.replace(/\D/g, '').slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.slice(0, 3) + '.' + d.slice(3);
    if (d.length <= 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  },
  cep: function (texto) {
    const d = texto.replace(/\D/g, '').slice(0, 8);
    if (d.length <= 5) return d;
    return d.slice(0, 5) + '-' + d.slice(5);
  },
  data: function (texto) {
    const d = texto.replace(/\D/g, '').slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
    return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  },
};

document.querySelectorAll('[data-formato]').forEach(function (campo) {
  campo.addEventListener('input', function () {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  });
});

const abas = document.querySelectorAll('.aba');
abas.forEach(function (aba) {
  aba.addEventListener('click', function () {
    abas.forEach(function (outra) { outra.classList.toggle('ativa', outra === aba); });
    document.querySelectorAll('.formulario').forEach(function (formulario) {
      formulario.classList.toggle('ativa', formulario.id === aba.dataset.alvo);
    });
  });
});

document.querySelectorAll('.formulario').forEach(function (formulario) {
  formulario.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    const dados = { perfil: formulario.dataset.perfil };
    new FormData(formulario).forEach(function (valor, chave) { dados[chave] = valor; });
    const resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.();
    const caixa = formulario.querySelector('.erros');
    if (resultado.erros && resultado.erros.length > 0) {
      caixa.replaceChildren();
      resultado.erros.forEach(function (mensagem) {
        const p = document.createElement('p');
        p.textContent = mensagem;
        caixa.appendChild(p);
      });
      caixa.hidden = false;
    } else {
      document.getElementById('oficio').textContent = resultado.oficio;
      document.getElementById('area-solicitacao').hidden = true;
      document.getElementById('confirmacao').hidden = false;
      window.scrollTo(0, 0);
    }
  });
});
