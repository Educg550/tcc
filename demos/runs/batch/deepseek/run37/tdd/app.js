(function () {
  'use strict';

  var abas = document.querySelectorAll('.aba');
  var formularios = document.querySelectorAll('.formulario');

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) {
        outra.classList.toggle('ativa', outra === aba);
      });
      formularios.forEach(function (form) {
        form.hidden = form.dataset.aba !== aba.dataset.aba;
      });
    });
  });

  function digitos(valor) {
    return valor.replace(/\D/g, '');
  }

  function formataValor(valor) {
    var d = digitos(valor);
    if (d === '') {
      return '';
    }
    var partes = (parseInt(d, 10) / 100).toFixed(2).split('.');
    var inteiro = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + inteiro + ',' + partes[1];
  }

  function formataCPF(valor) {
    var d = digitos(valor).slice(0, 11);
    if (d.length > 9) {
      return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
    }
    if (d.length > 6) {
      return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    }
    if (d.length > 3) {
      return d.slice(0, 3) + '.' + d.slice(3);
    }
    return d;
  }

  function formataCEP(valor) {
    var d = digitos(valor).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }

  function formataData(valor) {
    var d = digitos(valor).slice(0, 8);
    if (d.length > 4) {
      return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    }
    if (d.length > 2) {
      return d.slice(0, 2) + '/' + d.slice(2);
    }
    return d;
  }

  var mascaras = {
    valor: formataValor,
    cpf: formataCPF,
    cep: formataCEP,
    data_nascimento: formataData
  };

  document.querySelectorAll('input').forEach(function (input) {
    var mascara = mascaras[input.name];
    if (mascara) {
      input.addEventListener('blur', function () {
        input.value = mascara(input.value);
      });
    }
  });

  function mostraConfirmacao(oficio) {
    var conteudo = document.querySelector('.conteudo');
    var titulo = document.createElement('h2');
    titulo.className = 'titulo-confirmacao';
    titulo.textContent = 'Solicitação registrada';
    var pre = document.createElement('pre');
    pre.className = 'oficio';
    pre.textContent = oficio;
    conteudo.replaceChildren(titulo, pre);
  }

  formularios.forEach(function (form) {
    form.addEventListener('submit', function (evento) {
      evento.preventDefault();
      var dados = {};
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = valor;
      });
      dados.aba = form.dataset.aba;
      fetch('/solicitar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (resultado) {
          var areaErros = form.querySelector('.erros');
          if (resultado.erros && resultado.erros.length) {
            areaErros.textContent = resultado.erros.join('\n');
            areaErros.hidden = false;
            return;
          }
          mostraConfirmacao(resultado.oficio);
        });
    });
  });
}());
