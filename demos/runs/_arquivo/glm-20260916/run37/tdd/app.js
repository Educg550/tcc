'use strict';

function apenasDigitos(valor) {
  return valor.replace(/[^0-9]/g, '');
}

function formatarMoeda(campo) {
  const digitos = apenasDigitos(campo.value).slice(0, 12);
  if (!digitos) {
    campo.value = '';
    return;
  }
  const centavos = parseInt(digitos, 10);
  const reais = Math.floor(centavos / 100).toLocaleString('pt-BR');
  campo.value = 'R$ ' + reais + ',' + String(centavos % 100).padStart(2, '0');
}

function formatarCpf(campo) {
  const d = apenasDigitos(campo.value).slice(0, 11);
  let texto = d.slice(0, 3);
  if (d.length > 3) texto += '.' + d.slice(3, 6);
  if (d.length > 6) texto += '.' + d.slice(6, 9);
  if (d.length > 9) texto += '-' + d.slice(9);
  campo.value = texto;
}

function formatarCep(campo) {
  const d = apenasDigitos(campo.value).slice(0, 8);
  campo.value = d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(campo) {
  const d = apenasDigitos(campo.value).slice(0, 8);
  let texto = d.slice(0, 2);
  if (d.length > 2) texto += '/' + d.slice(2, 4);
  if (d.length > 4) texto += '/' + d.slice(4);
  campo.value = texto;
}

const formatadores = {
  'fmt-moeda': formatarMoeda,
  'fmt-cpf': formatarCpf,
  'fmt-cep': formatarCep,
  'fmt-data': formatarData
};

Object.keys(formatadores).forEach(function (classe) {
  document.querySelectorAll('.' + classe).forEach(function (campo) {
    campo.addEventListener('blur', function () {
      formatadores[classe](campo);
    });
  });
});

document.querySelectorAll('.aba').forEach(function (aba) {
  aba.addEventListener('click', function () {
    document.querySelectorAll('.aba').forEach(function (outra) {
      outra.classList.toggle('ativa', outra === aba);
    });
    document.querySelectorAll('.painel').forEach(function (painel) {
      painel.classList.toggle('oculto', painel.id !== aba.dataset.alvo);
    });
    document.getElementById('confirmacao').classList.add('oculto');
  });
});

document.querySelectorAll('.form-solicitacao').forEach(function (form) {
  form.addEventListener('submit', function (evento) {
    evento.preventDefault();
    const dados = { ABA: form.dataset.aba };
    form.querySelectorAll('input, select, textarea').forEach(function (campo) {
      const rotulo = campo.closest('label').querySelector('.rotulo');
      if (rotulo) {
        dados[rotulo.textContent.trim()] = campo.value;
      }
    });
    fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados)
    })
      .then(function (resposta) { return resposta.(); })
      .then(function (conteudo) {
        if (conteudo.erros && conteudo.erros.length > 0) {
          const lista = form.querySelector('.erros');
          lista.textContent = '';
          conteudo.erros.forEach(function (mensagem) {
            const item = document.createElement('p');
            item.textContent = mensagem;
            lista.appendChild(item);
          });
        } else if (conteudo.oficio) {
          document.getElementById('texto-oficio').textContent = conteudo.oficio;
          document.querySelectorAll('.painel').forEach(function (painel) {
            painel.classList.add('oculto');
          });
          document.querySelector('.navegacao-abas').classList.add('oculto');
          document.getElementById('confirmacao').classList.remove('oculto');
        }
      });
  });
});
