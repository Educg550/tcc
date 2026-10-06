'use strict';

function apenasDigitos(texto) {
  return texto.replace(/\D/g, '');
}

function formatarValor(campo) {
  const digitos = apenasDigitos(campo.value);
  if (!digitos) {
    campo.value = '';
    return;
  }
  const centavos = parseInt(digitos, 10);
  const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  campo.value = 'R$ ' + reais + ',' + String(centavos % 100).padStart(2, '0');
}

function formatarCpf(campo) {
  const d = apenasDigitos(campo.value).slice(0, 11);
  if (!d) {
    campo.value = '';
    return;
  }
  const partes = [d.slice(0, 3), d.slice(3, 6), d.slice(6, 9)].filter(Boolean);
  campo.value = partes.join('.') + (d.length > 9 ? '-' + d.slice(9) : '');
}

function formatarCep(campo) {
  const d = apenasDigitos(campo.value).slice(0, 8);
  campo.value = d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(campo) {
  const d = apenasDigitos(campo.value).slice(0, 8);
  if (d.length > 4) {
    campo.value = d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  } else if (d.length > 2) {
    campo.value = d.slice(0, 2) + '/' + d.slice(2);
  } else {
    campo.value = d;
  }
}

const FORMATADORES = {
  'VALOR SOLICITADO (R$)': formatarValor,
  'CPF (SEPARADOS POR PONTOS E TRAÇO)': formatarCpf,
  'CEP': formatarCep,
  'DATA DE NASCIMENTO': formatarData
};

document.querySelectorAll('.formulario input[name]').forEach(function (campo) {
  const formatador = FORMATADORES[campo.name];
  if (formatador) {
    campo.addEventListener('blur', function () { formatador(campo); });
  }
});

const abas = Array.from(document.querySelectorAll('.aba'));
const formularios = Array.from(document.querySelectorAll('.formulario'));

abas.forEach(function (aba) {
  aba.addEventListener('click', function () {
    abas.forEach(function (outra) { outra.classList.toggle('ativa', outra === aba); });
    formularios.forEach(function (form) {
      form.classList.toggle('oculta', form.id !== aba.dataset.form);
    });
  });
});

formularios.forEach(function (form) {
  form.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    const dados = {};
    form.querySelectorAll('[name]').forEach(function (campo) {
      dados[campo.name] = campo.value;
    });
    const areaErros = form.querySelector('.erros');
    areaErros.replaceChildren();
    let resultado;
    try {
      const resposta = await fetch('/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/' },
        body: JSON.stringify({ aba: form.id === 'form-alunos' ? 'alunos' : 'docentes', dados: dados })
      });
      resultado = await resposta.();
    } catch (erro) {
      resultado = { valido: false, erros: ['Não foi possível enviar a solicitação'] };
    }
    if (resultado.valido) {
      document.querySelector('.abas').classList.add('oculta');
      formularios.forEach(function (f) { f.classList.add('oculta'); });
      document.getElementById('oficio').textContent = resultado.oficio;
      document.getElementById('confirmacao').classList.remove('oculta');
    } else {
      resultado.erros.forEach(function (mensagem) {
        const linha = document.createElement('div');
        linha.className = 'erro';
        linha.textContent = mensagem;
        areaErros.appendChild(linha);
      });
    }
  });
});
