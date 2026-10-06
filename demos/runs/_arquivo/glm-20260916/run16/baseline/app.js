'use strict';

function apenasDigitos(valor) {
  return valor.replace(/\D/g, '');
}

function formatarValor(valor) {
  const digitos = apenasDigitos(valor).replace(/^0+(?=\d)/, '');
  if (!digitos) {
    return '';
  }
  const partes = digitos.padStart(3, '0');
  const centavos = partes.slice(-2);
  const reais = partes.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + reais + ',' + centavos;
}

function formatarCpf(valor) {
  const d = apenasDigitos(valor).slice(0, 11);
  let saida = d.slice(0, 3);
  if (d.length > 3) {
    saida += '.' + d.slice(3, 6);
  }
  if (d.length > 6) {
    saida += '.' + d.slice(6, 9);
  }
  if (d.length > 9) {
    saida += '-' + d.slice(9);
  }
  return saida;
}

function formatarCep(valor) {
  const d = apenasDigitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(valor) {
  const d = apenasDigitos(valor).slice(0, 8);
  let saida = d.slice(0, 2);
  if (d.length > 2) {
    saida += '/' + d.slice(2, 4);
  }
  if (d.length > 4) {
    saida += '/' + d.slice(4);
  }
  return saida;
}

const FORMATADORES = {
  valor: formatarValor,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData
};

document.querySelectorAll('input[data-fmt]').forEach(function (campo) {
  const formatar = FORMATADORES[campo.dataset.fmt];
  function aplicar() {
    campo.value = formatar(campo.value);
  }
  campo.addEventListener('input', aplicar);
  campo.addEventListener('blur', aplicar);
});

document.querySelectorAll('.aba').forEach(function (aba) {
  aba.addEventListener('click', function () {
    document.querySelectorAll('.aba').forEach(function (outra) {
      outra.classList.toggle('ativa', outra === aba);
    });
    document.querySelectorAll('.form').forEach(function (form) {
      form.hidden = form.id !== aba.dataset.alvo;
    });
  });
});

document.querySelectorAll('form.form').forEach(function (form) {
  form.addEventListener('submit', function (evento) {
    evento.preventDefault();
    const areaErros = form.querySelector('.erros');
    areaErros.textContent = '';
    const dados = { tipo: form.dataset.tipo };
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = valor;
    });
    fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados)
    })
      .then(function (resposta) {
        return resposta.();
      })
      .then(function (resultado) {
        if (resultado.oficio) {
          document.getElementById('formularios').hidden = true;
          document.getElementById('oficio').textContent = resultado.oficio;
          document.getElementById('confirmacao').hidden = false;
          return;
        }
        resultado.erros.forEach(function (mensagem) {
          const linha = document.createElement('p');
          linha.textContent = mensagem;
          areaErros.appendChild(linha);
        });
      });
  });
});
