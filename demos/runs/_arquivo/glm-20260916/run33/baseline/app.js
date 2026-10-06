'use strict';

const FORMATADORES = {
  valor: function (texto) {
    const digitos = texto.replace(/\D/g, '');
    if (!digitos) {
      return '';
    }
    const centavos = parseInt(digitos, 10);
    const inteiro = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + inteiro + ',' + String(centavos % 100).padStart(2, '0');
  },
  cpf: function (texto) {
    const d = texto.replace(/\D/g, '').slice(0, 11);
    let formatado = d.slice(0, 3);
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
    const d = texto.replace(/\D/g, '').slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  },
  data: function (texto) {
    const d = texto.replace(/\D/g, '').slice(0, 8);
    let formatado = d.slice(0, 2);
    if (d.length > 2) {
      formatado += '/' + d.slice(2, 4);
    }
    if (d.length > 4) {
      formatado += '/' + d.slice(4, 8);
    }
    return formatado;
  }
};

function iniciarFormatacao() {
  document.querySelectorAll('[data-formato]').forEach(function (campo) {
    const formatar = FORMATADORES[campo.dataset.formato];
    const aplicar = function () {
      campo.value = formatar(campo.value);
    };
    campo.addEventListener('input', aplicar);
    campo.addEventListener('blur', aplicar);
  });
}

function iniciarAbas() {
  const abas = document.querySelectorAll('.aba');
  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) {
        const ativa = outra === aba;
        outra.classList.toggle('ativa', ativa);
        document.getElementById(outra.dataset.alvo).hidden = !ativa;
      });
    });
  });
}

function coletarCampos(form) {
  const campos = {};
  form.querySelectorAll('[name]').forEach(function (campo) {
    campos[campo.name] = campo.value;
  });
  return campos;
}

function iniciarEnvio(form, tipo) {
  form.addEventListener('submit', function (evento) {
    evento.preventDefault();
    const quadroErros = form.querySelector('.erros');
    quadroErros.replaceChildren();
    fetch('/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify({ tipo: tipo, campos: coletarCampos(form) })
    })
      .then(function (resposta) {
        return resposta.();
      })
      .then(function (dados) {
        if (dados.ok) {
          document.getElementById('formulario-view').hidden = true;
          document.getElementById('oficio').textContent = dados.oficio;
          document.getElementById('confirmacao-view').hidden = false;
        } else {
          dados.erros.forEach(function (mensagem) {
            const paragrafo = document.createElement('p');
            paragrafo.textContent = mensagem;
            quadroErros.appendChild(paragrafo);
          });
        }
      });
  });
}

iniciarAbas();
iniciarFormatacao();
iniciarEnvio(document.getElementById('form-alunos'), 'alunos');
iniciarEnvio(document.getElementById('form-docentes'), 'docentes');
