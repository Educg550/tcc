'use strict';

const FORMATADORES = {
  moeda: function (digitos) {
    if (!digitos) {
      return '';
    }
    const centavos = parseInt(digitos, 10) || 0;
    const reais = Math.floor(centavos / 100);
    const resto = String(centavos % 100).padStart(2, '0');
    const milhar = String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + milhar + ',' + resto;
  },
  cpf: function (digitos) {
    const d = digitos.slice(0, 11);
    let formato = d.slice(0, 3);
    if (d.length > 3) {
      formato += '.' + d.slice(3, 6);
    }
    if (d.length > 6) {
      formato += '.' + d.slice(6, 9);
    }
    if (d.length > 9) {
      formato += '-' + d.slice(9, 11);
    }
    return formato;
  },
  cep: function (digitos) {
    const d = digitos.slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  },
  data: function (digitos) {
    const d = digitos.slice(0, 8);
    let formato = d.slice(0, 2);
    if (d.length > 2) {
      formato += '/' + d.slice(2, 4);
    }
    if (d.length > 4) {
      formato += '/' + d.slice(4, 8);
    }
    return formato;
  },
};

document.querySelectorAll('input[data-formato]').forEach(function (campo) {
  campo.addEventListener('blur', function () {
    const formatar = FORMATADORES[campo.dataset.formato];
    campo.value = formatar(campo.value.replace(/\D/g, ''));
  });
});

document.querySelectorAll('.aba').forEach(function (botao) {
  botao.addEventListener('click', function () {
    document.querySelectorAll('.aba').forEach(function (outra) {
      outra.classList.toggle('ativa', outra === botao);
    });
    const alunos = botao.dataset.aba === 'alunos';
    document.getElementById('form-alunos').hidden = !alunos;
    document.getElementById('form-docentes').hidden = alunos;
  });
});

async function enviarFormulario(formulario, aba) {
  const dados = { aba: aba };
  formulario.querySelectorAll('[name]').forEach(function (campo) {
    dados[campo.name] = campo.value.trim();
  });
  const resposta = await fetch('/api/solicitacao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/' },
    body: JSON.stringify(dados),
  });
  const corpo = await resposta.();
  if (corpo.ok) {
    document.querySelector('.abas').hidden = true;
    document.getElementById('formulario').hidden = true;
    document.getElementById('oficio').textContent = corpo.oficio;
    document.getElementById('confirmacao').hidden = false;
    return;
  }
  const caixa = formulario.querySelector('.erros');
  caixa.replaceChildren();
  corpo.erros.forEach(function (mensagem) {
    const paragrafo = document.createElement('p');
    paragrafo.textContent = mensagem;
    caixa.appendChild(paragrafo);
  });
  caixa.hidden = false;
}

document.getElementById('form-alunos').addEventListener('submit', function (evento) {
  evento.preventDefault();
  enviarFormulario(evento.target, 'ALUNOS');
});

document.getElementById('form-docentes').addEventListener('submit', function (evento) {
  evento.preventDefault();
  enviarFormulario(evento.target, 'DOCENTES');
});
