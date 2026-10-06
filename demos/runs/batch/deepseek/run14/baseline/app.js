(function () {
  'use strict';

  function apenasDigitos(valor) {
    return (valor || '').replace(/\D/g, '');
  }

  function separarMilhar(digitos) {
    return digitos.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  }

  function formatarValor(valor) {
    var digitos = apenasDigitos(valor);
    if (!digitos) { return ''; }
    var total = parseInt(digitos, 10);
    var reais = Math.floor(total / 100);
    var centavos = String(total % 100).padStart(2, '0');
    return 'R$ ' + separarMilhar(String(reais)) + ',' + centavos;
  }

  function formatarCPF(valor) {
    var d = apenasDigitos(valor).slice(0, 11);
    if (d.length !== 11) { return valor; }
    return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  }

  function formatarCEP(valor) {
    var d = apenasDigitos(valor).slice(0, 8);
    if (d.length !== 8) { return valor; }
    return d.slice(0, 5) + '-' + d.slice(5);
  }

  function formatarData(valor) {
    var d = apenasDigitos(valor).slice(0, 8);
    if (d.length !== 8) { return valor; }
    return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  }

  document.addEventListener('focusout', function (evento) {
    var campo = evento.target;
    if (!campo || !campo.name) { return; }
    if (campo.name === 'valor') { campo.value = formatarValor(campo.value); }
    else if (campo.name === 'cpf') { campo.value = formatarCPF(campo.value); }
    else if (campo.name === 'cep') { campo.value = formatarCEP(campo.value); }
    else if (campo.name === 'nascimento') { campo.value = formatarData(campo.value); }
  });

  var abas = document.querySelectorAll('.aba');
  var formularios = document.querySelectorAll('.formulario');

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) {
        outra.classList.toggle('ativa', outra === aba);
      });
      formularios.forEach(function (form) {
        form.classList.toggle('ativo', form.dataset.aba === aba.dataset.aba);
      });
    });
  });

  function mostrarErros(form, erros) {
    var caixa = form.querySelector('.erros');
    caixa.innerHTML = '';
    erros.forEach(function (mensagem) {
      var p = document.createElement('p');
      p.textContent = mensagem;
      caixa.appendChild(p);
    });
  }

  formularios.forEach(function (form) {
    form.addEventListener('submit', function (evento) {
      evento.preventDefault();

      var dados = { aba: form.dataset.aba };
      new FormData(form).forEach(function (valor, nome) {
        dados[nome] = valor;
      });

      fetch('/api/solicitar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (resultado) {
          mostrarErros(form, resultado.erros || []);
          if (resultado.ok) {
            document.getElementById('painel').hidden = true;
            document.getElementById('oficio').textContent = resultado.oficio;
            document.getElementById('confirmacao').hidden = false;
          }
        });
    });
  });
})();
