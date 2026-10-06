'use strict';

const FORMATADORES = {
  'VALOR SOLICITADO (R$)': formatarValor,
  'CPF (SEPARADOS POR PONTOS E TRAÇO)': formatarCpf,
  'CEP': formatarCep,
  'DATA DE NASCIMENTO': formatarData,
};

function digitos(texto) {
  return texto.replace(/\D/g, '');
}

function formatarValor(texto) {
  const centavos = digitos(texto);
  if (!centavos) {
    return '';
  }
  const numero = parseInt(centavos, 10);
  const reais = String(Math.trunc(numero / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + reais + ',' + String(numero % 100).padStart(2, '0');
}

function formatarCpf(texto) {
  const d = digitos(texto).slice(0, 11);
  if (!d) {
    return '';
  }
  if (d.length <= 3) {
    return d;
  }
  if (d.length <= 6) {
    return d.slice(0, 3) + '.' + d.slice(3);
  }
  if (d.length <= 9) {
    return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
  }
  return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
}

function formatarCep(texto) {
  const d = digitos(texto).slice(0, 8);
  if (d.length <= 5) {
    return d;
  }
  return d.slice(0, 5) + '-' + d.slice(5);
}

function formatarData(texto) {
  const d = digitos(texto).slice(0, 8);
  if (d.length <= 2) {
    return d;
  }
  if (d.length <= 4) {
    return d.slice(0, 2) + '/' + d.slice(2);
  }
  return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
}

function iniciarAbas() {
  const abas = document.querySelectorAll('.aba');
  const formularios = document.querySelectorAll('form.formulario');
  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) {
        outra.classList.toggle('ativa', outra === aba);
      });
      formularios.forEach(function (formulario) {
        formulario.hidden = formulario.dataset.aba !== aba.dataset.aba;
      });
    });
  });
}

function iniciarMascaras() {
  document.querySelectorAll('form.formulario [name]').forEach(function (campo) {
    const formatar = FORMATADORES[campo.name];
    if (formatar) {
      campo.addEventListener('blur', function () {
        campo.value = formatar(campo.value);
      });
    }
  });
}

function iniciarEnvio() {
  document.querySelectorAll('form.formulario').forEach(function (formulario) {
    formulario.addEventListener('submit', async function (evento) {
      evento.preventDefault();
      const dados = { aba: formulario.dataset.aba };
      formulario.querySelectorAll('[name]').forEach(function (campo) {
        let valor = campo.value.trim();
        if (campo.name === 'VALOR SOLICITADO (R$)') {
          valor = digitos(valor);
        }
        dados[campo.name] = valor;
      });
      const resposta = await fetch('/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/' },
        body: JSON.stringify(dados),
      });
      const retorno = await resposta.();
      const quadroDeErros = formulario.querySelector('.erros');
      if (retorno.erros && retorno.erros.length > 0) {
        quadroDeErros.replaceChildren(
          ...retorno.erros.map(function (mensagem) {
            const paragrafo = document.createElement('p');
            paragrafo.textContent = mensagem;
            return paragrafo;
          })
        );
        quadroDeErros.hidden = false;
        return;
      }
      document.getElementById('oficio').textContent = retorno.oficio;
      document.getElementById('formularios').hidden = true;
      document.getElementById('confirmacao').hidden = false;
    });
  });
}

iniciarAbas();
iniciarMascaras();
iniciarEnvio();
