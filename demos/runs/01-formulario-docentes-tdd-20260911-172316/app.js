document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.aba-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.aba-btn').forEach(function (b) {
        b.classList.remove('ativa');
      });
      btn.classList.add('ativa');
      var aba = btn.dataset.aba;
      document.getElementById('form-alunos').classList.toggle('ativa', aba === 'alunos');
      document.getElementById('form-docentes').classList.toggle('ativa', aba === 'docentes');
    });
  });

  function soDigitos(valor) {
    return valor.replace(/\D/g, '');
  }

  function formatarValor(valor) {
    var digitos = soDigitos(valor);
    if (!digitos) {
      return '';
    }
    var centavos = parseInt(digitos, 10);
    var reais = Math.floor(centavos / 100);
    var resto = centavos % 100;
    var reaisStr = String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    var restoStr = resto < 10 ? '0' + resto : String(resto);
    return 'R$ ' + reaisStr + ',' + restoStr;
  }

  function formatarCPF(valor) {
    var digitos = soDigitos(valor).slice(0, 11);
    if (digitos.length < 11) {
      return digitos;
    }
    return digitos.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
  }

  function formatarCEP(valor) {
    var digitos = soDigitos(valor).slice(0, 8);
    if (digitos.length < 8) {
      return digitos;
    }
    return digitos.replace(/(\d{5})(\d{3})/, '$1-$2');
  }

  function formatarData(valor) {
    var digitos = soDigitos(valor).slice(0, 8);
    if (digitos.length < 8) {
      return digitos;
    }
    return digitos.replace(/(\d{2})(\d{2})(\d{4})/, '$1/$2/$3');
  }

  document.querySelectorAll('.formato-valor').forEach(function (el) {
    el.addEventListener('blur', function () {
      el.value = formatarValor(el.value);
    });
  });
  document.querySelectorAll('.formato-cpf').forEach(function (el) {
    el.addEventListener('blur', function () {
      el.value = formatarCPF(el.value);
    });
  });
  document.querySelectorAll('.formato-cep').forEach(function (el) {
    el.addEventListener('blur', function () {
      el.value = formatarCEP(el.value);
    });
  });
  document.querySelectorAll('.formato-data').forEach(function (el) {
    el.addEventListener('blur', function () {
      el.value = formatarData(el.value);
    });
  });

  document.querySelectorAll('form.formulario').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var dados = {};
      form.querySelectorAll('[data-campo]').forEach(function (el) {
        var campo = el.dataset.campo;
        if (campo === 'VALOR SOLICITADO (R$)') {
          var digitos = soDigitos(el.value);
          dados[campo] = digitos ? parseInt(digitos, 10) : 0;
        } else {
          dados[campo] = el.value;
        }
      });

      fetch(form.dataset.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (corpo) {
          var areaErros = form.querySelector('.erros');
          if (corpo.erros && corpo.erros.length > 0) {
            areaErros.textContent = corpo.erros.join('\n');
          } else {
            areaErros.textContent = '';
            document.querySelectorAll('.formulario').forEach(function (f) {
              f.hidden = true;
            });
            document.querySelector('.abas').hidden = true;
            var confirmacao = document.getElementById('confirmacao');
            confirmacao.hidden = false;
            document.getElementById('oficio').textContent = corpo.oficio;
          }
        });
    });
  });
});
