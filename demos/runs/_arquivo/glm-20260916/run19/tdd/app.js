'use strict';

function soDigitos(texto) {
  return String(texto || '').replace(/\D/g, '');
}

function formatarValor(texto) {
  const digitos = soDigitos(texto).slice(0, 12);
  if (!digitos) {
    return '';
  }
  const centavos = parseInt(digitos, 10);
  const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + reais + ',' + String(centavos % 100).padStart(2, '0');
}

function formatarCpf(texto) {
  const d = soDigitos(texto).slice(0, 11);
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
  const d = soDigitos(texto).slice(0, 8);
  if (d.length <= 5) {
    return d;
  }
  return d.slice(0, 5) + '-' + d.slice(5);
}

function formatarData(texto) {
  const d = soDigitos(texto).slice(0, 8);
  if (d.length <= 2) {
    return d;
  }
  if (d.length <= 4) {
    return d.slice(0, 2) + '/' + d.slice(2);
  }
  return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
}

const MASCARAS = [
  ['valor', formatarValor],
  ['cpf', formatarCpf],
  ['cep', formatarCep],
  ['data_nascimento', formatarData]
];

const FORMULARIOS = {
  alunos: document.getElementById('form-alunos'),
  docentes: document.getElementById('form-docentes')
};

const ABAS = {
  alunos: document.getElementById('aba-alunos'),
  docentes: document.getElementById('aba-docentes')
};

function abrirAba(nome) {
  Object.keys(FORMULARIOS).forEach(function (chave) {
    const ativa = chave === nome;
    FORMULARIOS[chave].hidden = !ativa;
    ABAS[chave].classList.toggle('active', ativa);
    ABAS[chave].setAttribute('aria-selected', ativa ? 'true' : 'false');
  });
  document.getElementById('confirmacao').hidden = true;
}

Object.keys(ABAS).forEach(function (chave) {
  ABAS[chave].addEventListener('click', function () {
    abrirAba(chave);
  });
});

Object.keys(FORMULARIOS).forEach(function (chave) {
  const form = FORMULARIOS[chave];
  MASCARAS.forEach(function (par) {
    const campo = form.elements[par[0]];
    if (campo) {
      campo.addEventListener('blur', function () {
        campo.value = par[1](campo.value);
      });
    }
  });
  form.addEventListener('submit', function (evento) {
    evento.preventDefault();
    enviarSolicitacao(form);
  });
});

function enviarSolicitacao(form) {
  const caixa = form.querySelector('.erros');
  caixa.hidden = true;
  caixa.textContent = '';
  const dados = {};
  new FormData(form).forEach(function (valor, chave) {
    dados[chave] = String(valor).trim();
  });
  MASCARAS.forEach(function (par) {
    if (dados[par[0]]) {
      dados[par[0]] = par[1](dados[par[0]]);
    }
  });
  fetch('/api/solicitacao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/' },
    body: JSON.stringify(dados)
  })
    .then(function (resposta) {
      return resposta.();
    })
    .then(function (corpo) {
      if (corpo.erros && corpo.erros.length) {
        caixa.textContent = corpo.erros.join('\n');
        caixa.hidden = false;
      } else {
        document.getElementById('oficio').textContent = corpo.oficio;
        FORMULARIOS.alunos.hidden = true;
        FORMULARIOS.docentes.hidden = true;
        document.getElementById('confirmacao').hidden = false;
      }
    });
}
