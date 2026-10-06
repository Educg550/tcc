(function () {
  'use strict';

  var FORMATADORES = {
    moeda: function (digitos) {
      if (!digitos) {
        return '';
      }
      digitos = digitos.replace(/^0+(?=\d)/, '');
      var centavos = digitos.padStart(3, '0');
      var inteiro = centavos.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      return 'R$ ' + inteiro + ',' + centavos.slice(-2);
    },
    cpf: function (digitos) {
      digitos = digitos.slice(0, 11);
      if (digitos.length > 9) {
        return digitos.slice(0, 3) + '.' + digitos.slice(3, 6) + '.' + digitos.slice(6, 9) + '-' + digitos.slice(9);
      }
      if (digitos.length > 6) {
        return digitos.slice(0, 3) + '.' + digitos.slice(3, 6) + '.' + digitos.slice(6);
      }
      if (digitos.length > 3) {
        return digitos.slice(0, 3) + '.' + digitos.slice(3);
      }
      return digitos;
    },
    cep: function (digitos) {
      digitos = digitos.slice(0, 8);
      return digitos.length > 5 ? digitos.slice(0, 5) + '-' + digitos.slice(5) : digitos;
    },
    data: function (digitos) {
      digitos = digitos.slice(0, 8);
      if (digitos.length > 4) {
        return digitos.slice(0, 2) + '/' + digitos.slice(2, 4) + '/' + digitos.slice(4);
      }
      if (digitos.length > 2) {
        return digitos.slice(0, 2) + '/' + digitos.slice(2);
      }
      return digitos;
    }
  };

  var abas = document.querySelectorAll('.aba');
  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (outra) {
        outra.classList.remove('ativa');
      });
      aba.classList.add('ativa');
      document.querySelectorAll('.formulario').forEach(function (formulario) {
        formulario.classList.add('oculto');
      });
      document.getElementById('form-' + aba.dataset.aba).classList.remove('oculto');
    });
  });

  document.querySelectorAll('[data-formato]').forEach(function (campo) {
    campo.addEventListener('blur', function () {
      var formatar = FORMATADORES[campo.dataset.formato];
      if (formatar) {
        campo.value = formatar(campo.value.replace(/\D/g, ''));
      }
    });
  });

  function mostrarErros(formulario, mensagens) {
    var area = formulario.querySelector('.erros');
    area.innerHTML = '';
    mensagens.forEach(function (mensagem) {
      var item = document.createElement('div');
      item.className = 'erro';
      item.textContent = mensagem;
      area.appendChild(item);
    });
    window.scrollTo(0, 0);
  }

  function enviar(formulario, aba) {
    var dados = { aba: aba };
    formulario.querySelectorAll('[name]').forEach(function (campo) {
      dados[campo.name] = campo.value.trim();
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
        if (corpo.erros) {
          mostrarErros(formulario, corpo.erros);
        } else {
          document.getElementById('conteudo').classList.add('oculto');
          document.getElementById('oficio').textContent = corpo.oficio;
          document.getElementById('confirmacao').classList.remove('oculto');
          window.scrollTo(0, 0);
        }
      });
  }

  document.getElementById('form-alunos').addEventListener('submit', function (evento) {
    evento.preventDefault();
    enviar(evento.target, 'ALUNOS');
  });

  document.getElementById('form-docentes').addEventListener('submit', function (evento) {
    evento.preventDefault();
    enviar(evento.target, 'DOCENTES');
  });
})();
