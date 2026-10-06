document.addEventListener('DOMContentLoaded', function () {
  var abas = document.querySelectorAll('.aba');
  var formularios = document.querySelectorAll('.formulario');
  var conteudo = document.getElementById('conteudo');
  var nav = document.querySelector('.abas');
  var confirmacao = document.getElementById('confirmacao');
  var oficio = document.getElementById('oficio');

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      var alvo = aba.dataset.aba;
      abas.forEach(function (a) {
        a.classList.toggle('ativa', a.dataset.aba === alvo);
      });
      formularios.forEach(function (f) {
        f.classList.toggle('ativa', f.dataset.aba === alvo);
      });
    });
  });

  function soDigitos(valor) {
    var saida = '';
    for (var i = 0; i < valor.length; i++) {
      var c = valor.charAt(i);
      if (c >= '0' && c <= '9') {
        saida += c;
      }
    }
    return saida;
  }

  function formataValor(valor) {
    var d = soDigitos(valor);
    if (!d) {
      return '';
    }
    var n = parseInt(d, 10);
    var reais = Math.floor(n / 100).toLocaleString('pt-BR');
    var centavos = String(n % 100).padStart(2, '0');
    return 'R$ ' + reais + ',' + centavos;
  }

  function formataCPF(valor) {
    var d = soDigitos(valor).slice(0, 11);
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
    var d = soDigitos(valor).slice(0, 8);
    if (d.length > 5) {
      return d.slice(0, 5) + '-' + d.slice(5);
    }
    return d;
  }

  function formataData(valor) {
    var d = soDigitos(valor).slice(0, 8);
    if (d.length > 4) {
      return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    }
    if (d.length > 2) {
      return d.slice(0, 2) + '/' + d.slice(2);
    }
    return d;
  }

  var formatadores = {
    valor: formataValor,
    cpf: formataCPF,
    cep: formataCEP,
    data_nascimento: formataData
  };

  document.querySelectorAll('input').forEach(function (campo) {
    var formatar = formatadores[campo.name];
    if (formatar) {
      campo.addEventListener('blur', function () {
        campo.value = formatar(campo.value);
      });
    }
  });

  formularios.forEach(function (form) {
    form.addEventListener('submit', function (evento) {
      evento.preventDefault();
      var errosBox = form.querySelector('.erros');
      errosBox.hidden = true;

      var dados = {};
      form.querySelectorAll('input, select, textarea').forEach(function (campo) {
        if (campo.name) {
          dados[campo.name] = campo.value;
        }
      });
      dados.aba = form.dataset.aba;
      dados.valor = soDigitos(dados.valor || '');

      fetch('/api/' + form.dataset.aba, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      }).then(function (resposta) {
        return resposta.text().then(function (texto) {
          if (resposta.ok) {
            oficio.textContent = texto;
            conteudo.hidden = true;
            nav.hidden = true;
            confirmacao.hidden = false;
          } else {
            errosBox.textContent = texto;
            errosBox.hidden = false;
          }
        });
      });
    });
  });
});
