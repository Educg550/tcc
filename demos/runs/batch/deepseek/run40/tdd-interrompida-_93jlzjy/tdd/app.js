// Formatação dos campos (funções puras, sem acesso ao DOM).

function formatarValor(digitos) {
  var d = String(digitos).replace(/[^0-9]/g, '').replace(/^0+/, '');
  while (d.length < 3) d = '0' + d;
  var inteiros = d.slice(0, -2).replace(/([0-9])(?=([0-9]{3})+$)/g, '$1.');
  return 'R$ ' + inteiros + ',' + d.slice(-2);
}

function formatarCPF(digitos) {
  var d = String(digitos).replace(/[^0-9]/g, '').slice(0, 11);
  var saida = [d.slice(0, 3), d.slice(3, 6), d.slice(6, 9)].filter(Boolean).join('.');
  if (d.length > 9) saida += '-' + d.slice(9);
  return saida;
}

function formatarCEP(digitos) {
  var d = String(digitos).replace(/[^0-9]/g, '').slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(digitos) {
  var d = String(digitos).replace(/[^0-9]/g, '').slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
  return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
}

if (typeof globalThis !== 'undefined') {
  globalThis.formatarValor = formatarValor;
  globalThis.formatarCPF = formatarCPF;
  globalThis.formatarCEP = formatarCEP;
  globalThis.formatarData = formatarData;
}

// Tela

var MASCARAS = {
  valor: formatarValor,
  cpf: formatarCPF,
  cep: formatarCEP,
  data_nascimento: formatarData
};

function iniciar() {
  var abas = Array.prototype.slice.call(document.querySelectorAll('.aba'));
  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) {
        var ativa = outra === aba;
        outra.classList.toggle('ativa', ativa);
        outra.setAttribute('aria-selected', ativa ? 'true' : 'false');
      });
      Array.prototype.forEach.call(document.querySelectorAll('.painel'), function (painel) {
        painel.classList.toggle('visivel', painel.id === 'painel-' + aba.dataset.aba);
      });
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll('input, textarea'), function (campo) {
    var mascara = MASCARAS[campo.name];
    if (!mascara) return;
    campo.addEventListener('blur', function () {
      campo.value = mascara(campo.value);
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll('.solicitacao'), function (form) {
    form.addEventListener('submit', function (evento) {
      evento.preventDefault();
      enviar(form);
    });
  });
}

function enviar(form) {
  var dados = { aba: form.dataset.aba };
  new FormData(form).forEach(function (valor, campo) {
    dados[campo] = valor;
  });
  fetch('/solicitacao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados)
  }).then(function (resposta) {
    return resposta.json().then(function (corpo) {
      if (resposta.ok) {
        mostrarConfirmacao(corpo.oficio);
      } else {
        mostrarErros(form, corpo.erros || []);
      }
    });
  });
}

function mostrarErros(form, erros) {
  var caixa = form.querySelector('.erros');
  caixa.textContent = '';
  erros.forEach(function (erro) {
    var linha = document.createElement('span');
    linha.textContent = erro;
    caixa.appendChild(linha);
  });
  caixa.hidden = erros.length === 0;
}

function mostrarConfirmacao(oficio) {
  document.querySelector('main').hidden = true;
  document.getElementById('oficio').textContent = oficio;
  document.getElementById('confirmacao').hidden = false;
  window.scrollTo(0, 0);
}

if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', iniciar);
}
