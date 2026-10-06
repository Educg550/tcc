'use strict';

var FORMATADORES = {
  moeda: function (texto) {
    var digitos = texto.replace(/\D/g, '');
    if (!digitos) {
      return '';
    }
    var total = parseInt(digitos, 10);
    var centavos = String(total % 100).padStart(2, '0');
    var inteiro = String(Math.floor(total / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + inteiro + ',' + centavos;
  },
  cpf: function (texto) {
    var d = texto.replace(/\D/g, '').slice(0, 11);
    var formatado = d.slice(0, 3);
    if (d.length > 3) {
      formatado += '.' + d.slice(3, 6);
    }
    if (d.length > 6) {
      formatado += '.' + d.slice(6, 9);
    }
    if (d.length > 9) {
      formatado += '-' + d.slice(9, 11);
    }
    return formatado;
  },
  cep: function (texto) {
    var d = texto.replace(/\D/g, '').slice(0, 8);
    if (d.length <= 5) {
      return d;
    }
    return d.slice(0, 5) + '-' + d.slice(5);
  },
  data: function (texto) {
    var d = texto.replace(/\D/g, '').slice(0, 8);
    if (d.length > 4) {
      return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    }
    if (d.length > 2) {
      return d.slice(0, 2) + '/' + d.slice(2);
    }
    return d;
  }
};

document.querySelectorAll('input[data-formato]').forEach(function (campo) {
  campo.addEventListener('blur', function () {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  });
});

document.querySelectorAll('.aba').forEach(function (botao) {
  botao.addEventListener('click', function () {
    document.querySelectorAll('.aba').forEach(function (outra) {
      outra.classList.toggle('ativa', outra === botao);
      outra.setAttribute('aria-selected', outra === botao ? 'true' : 'false');
    });
    document.getElementById('painel-alunos').hidden = botao.dataset.aba !== 'ALUNOS';
    document.getElementById('painel-docentes').hidden = botao.dataset.aba !== 'DOCENTES';
    document.getElementById('confirmacao').hidden = true;
  });
});

document.querySelectorAll('form[data-aba]').forEach(function (formulario) {
  formulario.addEventListener('submit', function (evento) {
    evento.preventDefault();
    enviar(formulario);
  });
});

async function enviar(formulario) {
  var dados = { aba: formulario.dataset.aba };
  formulario.querySelectorAll('.campo').forEach(function (campo) {
    var controle = campo.querySelector('input, select, textarea');
    var rotulo = campo.querySelector('label').textContent.trim();
    dados[rotulo] = controle.value.trim();
  });
  var resposta = await fetch('/solicitar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/' },
    body: JSON.stringify(dados)
  });
  var corpo = await resposta.();
  if (corpo.ok) {
    document.getElementById('oficio').textContent = corpo.oficio;
    document.getElementById('painel-alunos').hidden = true;
    document.getElementById('painel-docentes').hidden = true;
    document.getElementById('confirmacao').hidden = false;
    document.querySelector('.conteudo').scrollTop = 0;
    return;
  }
  var lista = formulario.querySelector('.erros');
  lista.innerHTML = '';
  corpo.erros.forEach(function (mensagem) {
    var item = document.createElement('li');
    item.textContent = mensagem;
    lista.appendChild(item);
  });
  lista.hidden = false;
}
