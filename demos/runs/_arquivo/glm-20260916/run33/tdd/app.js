'use strict';

const formatadores = {
  moeda: function (valor) {
    const digitos = valor.replace(/\D/g, '');
    if (!digitos) {
      return '';
    }
    const centavos = parseInt(digitos, 10);
    const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + reais + ',' + String(centavos % 100).padStart(2, '0');
  },
  cpf: function (valor) {
    const d = valor.replace(/\D/g, '').slice(0, 11);
    let r = d;
    if (d.length > 9) {
      r = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
    } else if (d.length > 6) {
      r = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    } else if (d.length > 3) {
      r = d.slice(0, 3) + '.' + d.slice(3);
    }
    return r;
  },
  cep: function (valor) {
    const d = valor.replace(/\D/g, '').slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  },
  data: function (valor) {
    const d = valor.replace(/\D/g, '').slice(0, 8);
    let r = d;
    if (d.length > 4) {
      r = d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    } else if (d.length > 2) {
      r = d.slice(0, 2) + '/' + d.slice(2);
    }
    return r;
  },
};

document.querySelectorAll('[data-formato]').forEach(function (campo) {
  campo.addEventListener('blur', function () {
    campo.value = formatadores[campo.dataset.formato](campo.value);
  });
});

function abrirAba(alvo) {
  document.querySelectorAll('.aba').forEach(function (aba) {
    aba.classList.toggle('ativa', aba.dataset.alvo === alvo);
  });
  document.querySelectorAll('.painel').forEach(function (painel) {
    painel.hidden = painel.id !== alvo;
  });
}

document.querySelectorAll('.aba').forEach(function (aba) {
  aba.addEventListener('click', function () {
    abrirAba(aba.dataset.alvo);
  });
});

document.querySelectorAll('form.solicitacao').forEach(function (form) {
  form.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    const dados = { aba: form.dataset.aba };
    form.querySelectorAll('input, select, textarea').forEach(function (campo) {
      dados[campo.name] = campo.value;
    });
    const resposta = await fetch('/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados),
    });
    const corpo = await resposta.();
    const caixa = form.querySelector('.erros');
    if (resposta.ok) {
      caixa.hidden = true;
      document.getElementById('oficio').textContent = corpo.oficio;
      document.getElementById('confirmacao').hidden = false;
      document.querySelector('.abas').hidden = true;
      document.querySelectorAll('.painel').forEach(function (painel) {
        painel.hidden = true;
      });
    } else {
      caixa.textContent = '';
      corpo.erros.forEach(function (mensagem) {
        const linha = document.createElement('div');
        linha.textContent = mensagem;
        caixa.appendChild(linha);
      });
      caixa.hidden = false;
    }
  });
});

document.getElementById('voltar').addEventListener('click', function () {
  document.getElementById('confirmacao').hidden = true;
  document.querySelector('.abas').hidden = false;
  abrirAba(document.querySelector('.aba.ativa').dataset.alvo);
});
