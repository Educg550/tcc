'use strict';

const FORMATADORES = {
  'VALOR SOLICITADO (R$)': formatarMoeda,
  'CPF (SEPARADOS POR PONTOS E TRAÇO)': formatarCpf,
  'CEP': formatarCep,
  'DATA DE NASCIMENTO': formatarData
};

function soDigitos(texto) {
  return (texto || '').replace(/\D/g, '');
}

function formatarMoeda(texto) {
  const digitado = soDigitos(texto);
  if (!digitado) {
    return '';
  }
  const centavos = parseInt(digitado, 10);
  const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + reais + ',' + String(centavos % 100).padStart(2, '0');
}

function formatarCpf(texto) {
  const n = soDigitos(texto).slice(0, 11);
  let saida = n.slice(0, 3);
  if (n.length > 3) saida += '.' + n.slice(3, 6);
  if (n.length > 6) saida += '.' + n.slice(6, 9);
  if (n.length > 9) saida += '-' + n.slice(9);
  return saida;
}

function formatarCep(texto) {
  const n = soDigitos(texto).slice(0, 8);
  if (n.length > 5) return n.slice(0, 5) + '-' + n.slice(5);
  return n;
}

function formatarData(texto) {
  const n = soDigitos(texto).slice(0, 8);
  let saida = n.slice(0, 2);
  if (n.length > 2) saida += '/' + n.slice(2, 4);
  if (n.length > 4) saida += '/' + n.slice(4, 8);
  return saida;
}

document.querySelectorAll('.aba').forEach(function (botao) {
  botao.addEventListener('click', function () {
    document.querySelectorAll('.aba').forEach(function (outra) {
      outra.classList.toggle('ativa', outra === botao);
    });
    document.querySelectorAll('.formulario').forEach(function (formulario) {
      formulario.classList.toggle('ativo', formulario.id === botao.dataset.aba);
    });
  });
});

document.querySelectorAll('input').forEach(function (campo) {
  const formatar = FORMATADORES[campo.name];
  if (formatar) {
    campo.addEventListener('blur', function () {
      campo.value = formatar(campo.value);
    });
  }
});

document.querySelectorAll('.formulario').forEach(function (formulario) {
  formulario.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    const corpo = { aba: formulario.dataset.aba };
    formulario.querySelectorAll('[name]').forEach(function (campo) {
      corpo[campo.name] = campo.value;
    });
    const resposta = await fetch('/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(corpo)
    });
    const saida = await resposta.();
    const caixa = formulario.querySelector('.erros');
    if (saida.oficio) {
      caixa.hidden = true;
      document.querySelectorAll('.formulario').forEach(function (outra) {
        outra.classList.remove('ativo');
      });
      document.querySelector('.abas').hidden = true;
      document.getElementById('oficio').textContent = saida.oficio;
      document.getElementById('confirmacao').hidden = false;
    } else {
      caixa.textContent = '';
      (saida.erros || []).forEach(function (mensagem) {
        const linha = document.createElement('p');
        linha.textContent = mensagem;
        caixa.appendChild(linha);
      });
      caixa.hidden = false;
    }
  });
});
