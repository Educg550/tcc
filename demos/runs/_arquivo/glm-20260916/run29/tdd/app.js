(function () {
  'use strict';

  function digitos(texto) {
    return String(texto || '').replace(/[^0-9]/g, '');
  }

  function separarMilhar(reais) {
    var saida = '';
    var contador = 0;
    for (var i = reais.length - 1; i >= 0; i = i - 1) {
      saida = reais.charAt(i) + saida;
      contador = contador + 1;
      if (contador % 3 === 0 && i > 0) {
        saida = '.' + saida;
      }
    }
    return saida;
  }

  function formatarMoeda(campo) {
    var d = digitos(campo.value);
    if (!d) {
      campo.value = '';
      return;
    }
    var centavos = parseInt(d, 10);
    var reais = String(Math.floor(centavos / 100));
    var resto = String(centavos % 100);
    while (resto.length < 2) {
      resto = '0' + resto;
    }
    campo.value = 'R$ ' + separarMilhar(reais) + ',' + resto;
  }

  function formatarCpf(campo) {
    var d = digitos(campo.value).slice(0, 11);
    var texto = d.slice(0, 3);
    if (d.length > 3) { texto = texto + '.' + d.slice(3, 6); }
    if (d.length > 6) { texto = texto + '.' + d.slice(6, 9); }
    if (d.length > 9) { texto = texto + '-' + d.slice(9); }
    campo.value = texto;
  }

  function formatarCep(campo) {
    var d = digitos(campo.value).slice(0, 8);
    campo.value = d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }

  function formatarData(campo) {
    var d = digitos(campo.value).slice(0, 8);
    var texto = d.slice(0, 2);
    if (d.length > 2) { texto = texto + '/' + d.slice(2, 4); }
    if (d.length > 4) { texto = texto + '/' + d.slice(4); }
    campo.value = texto;
  }

  var FORMATA = {
    valor: formatarMoeda,
    cpf: formatarCpf,
    cep: formatarCep,
    data_nascimento: formatarData
  };

  document.addEventListener('blur', function (evento) {
    var formatar = FORMATA[evento.target.name];
    if (formatar) { formatar(evento.target); }
  }, true);

  var abas = Array.prototype.slice.call(document.querySelectorAll('.aba'));
  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) { outra.classList.remove('aba-ativa'); });
      aba.classList.add('aba-ativa');
      Array.prototype.forEach.call(document.querySelectorAll('.painel'), function (painel) {
        painel.classList.add('oculto');
      });
      document.getElementById('painel-' + aba.getAttribute('data-aba')).classList.remove('oculto');
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll('form.solicitacao'), function (form) {
    form.addEventListener('submit', function (evento) {
      evento.preventDefault();
      var dados = {};
      Array.prototype.forEach.call(form.elements, function (campo) {
        if (campo.name) { dados[campo.name] = campo.value; }
      });
      fetch('/api/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/' },
        body: JSON.stringify(dados)
      }).then(function (resposta) { return resposta.(); }).then(function (conteudo) {
        if (conteudo.oficio) {
          document.getElementById('texto-oficio').textContent = conteudo.oficio;
          document.getElementById('formularios').classList.add('oculto');
          document.getElementById('confirmacao').classList.remove('oculto');
        } else {
          var caixa = form.querySelector('.erros');
          caixa.textContent = '';
          (conteudo.erros || []).forEach(function (mensagem) {
            var linha = document.createElement('p');
            linha.textContent = mensagem;
            caixa.appendChild(linha);
          });
          caixa.classList.remove('oculto');
        }
      });
    });
  });
})();
