(function () {
  'use strict';

  var URL_SOLICITACAO = '/api/solicitacoes';

  function digitos(texto) {
    return (texto || '').replace(/\D/g, '');
  }

  function comMilhar(numero) {
    return String(numero).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  }

  function formatarValor(campo) {
    var d = digitos(campo.value);
    if (!d) {
      campo.value = '';
      return;
    }
    var centavos = parseInt(d, 10);
    campo.value = 'R$ ' + comMilhar(Math.floor(centavos / 100)) + ',' +
      String(centavos % 100).padStart(2, '0');
  }

  function formatarCpf(campo) {
    campo.value = digitos(campo.value).slice(0, 11)
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
  }

  function formatarCep(campo) {
    campo.value = digitos(campo.value).slice(0, 8).replace(/(\d{5})(\d)/, '$1-$2');
  }

  function formatarData(campo) {
    campo.value = digitos(campo.value).slice(0, 8)
      .replace(/(\d{2})(\d)/, '$1/$2')
      .replace(/(\d{2})(\d)/, '$1/$2');
  }

  var FORMATADORES = {
    valor: formatarValor,
    cpf: formatarCpf,
    cep: formatarCep,
    data: formatarData
  };

  document.querySelectorAll('input[data-formato]').forEach(function (campo) {
    var formatar = FORMATADORES[campo.getAttribute('data-formato')];
    campo.addEventListener('blur', function () { formatar(campo); });
  });

  var abas = document.querySelectorAll('.aba');
  var paineis = {
    alunos: document.getElementById('painel-alunos'),
    docentes: document.getElementById('painel-docentes')
  };

  function abrirAba(nome) {
    abas.forEach(function (aba) {
      var ativa = aba.getAttribute('data-aba') === nome;
      aba.classList.toggle('ativa', ativa);
      aba.setAttribute('aria-selected', ativa ? 'true' : 'false');
    });
    paineis.alunos.hidden = nome !== 'alunos';
    paineis.docentes.hidden = nome !== 'docentes';
    document.getElementById('confirmacao').hidden = true;
  }

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abrirAba(aba.getAttribute('data-aba'));
    });
  });

  document.querySelectorAll('form.solicitacao').forEach(function (form) {
    form.addEventListener('submit', function (evento) {
      evento.preventDefault();
      var caixa = form.querySelector('.erros');
      caixa.hidden = true;
      caixa.textContent = '';
      var dados = { aba: form.getAttribute('data-aba') };
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = valor;
      });
      fetch(URL_SOLICITACAO, {
        method: 'POST',
        headers: { 'Content-Type': 'application/' },
        body: JSON.stringify(dados)
      }).then(function (resposta) {
        return resposta.();
      }).then(function (resultado) {
        if (resultado.ok) {
          document.getElementById('oficio').textContent = resultado.oficio;
          document.getElementById('formulario').hidden = true;
          document.getElementById('confirmacao').hidden = false;
          window.scrollTo(0, 0);
        } else {
          resultado.erros.forEach(function (mensagem) {
            var paragrafo = document.createElement('p');
            paragrafo.textContent = mensagem;
            caixa.appendChild(paragrafo);
          });
          caixa.hidden = false;
        }
      });
    });
  });
})();
