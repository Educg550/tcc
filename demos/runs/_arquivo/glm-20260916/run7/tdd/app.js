'use strict';

function soDigitos(texto) {
  return (texto || '').replace(/\D/g, '');
}

const formatacoes = {
  moeda: function (campo) {
    const digitado = soDigitos(campo.value);
    if (!digitado) {
      campo.value = '';
      return;
    }
    const centavos = parseInt(digitado, 10);
    const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    campo.value = 'R$ ' + reais + ',' + String(centavos % 100).padStart(2, '0');
  },
  cpf: function (campo) {
    const digitado = soDigitos(campo.value);
    if (digitado.length === 11) {
      campo.value = digitado.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3-$4');
    }
  },
  cep: function (campo) {
    const digitado = soDigitos(campo.value);
    if (digitado.length === 8) {
      campo.value = digitado.replace(/^(\d{5})(\d{3})$/, '$1-$2');
    }
  },
  data: function (campo) {
    const digitado = soDigitos(campo.value);
    if (digitado.length === 8) {
      campo.value = digitado.replace(/^(\d{2})(\d{2})(\d{4})$/, '$1/$2/$3');
    }
  },
};

Object.keys(formatacoes).forEach(function (classe) {
  document.querySelectorAll('.' + classe).forEach(function (campo) {
    campo.addEventListener('blur', function () {
      formatacoes[classe](campo);
    });
  });
});

function abrirAba(nome) {
  document.querySelectorAll('.aba').forEach(function (aba) {
    aba.classList.toggle('ativa', aba.dataset.aba === nome);
  });
  document.querySelectorAll('.formulario').forEach(function (form) {
    form.hidden = form.id !== 'form-' + nome;
  });
}

document.querySelectorAll('.aba').forEach(function (aba) {
  aba.addEventListener('click', function () {
    abrirAba(aba.dataset.aba);
  });
});

document.querySelectorAll('.formulario').forEach(function (form) {
  form.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    const dados = {};
    new FormData(form).forEach(function (valor, nome) {
      dados[nome] = valor;
    });
    const resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.();
    if (resultado.oficio) {
      document.getElementById('formularios').hidden = true;
      document.getElementById('oficio').textContent = resultado.oficio;
      document.getElementById('confirmacao').hidden = false;
    } else {
      const mensagens = form.querySelector('.mensagens');
      mensagens.textContent = (resultado.erros || []).join('\n');
      mensagens.hidden = false;
    }
  });
});
