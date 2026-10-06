(function () {
  'use strict';

  var abas = document.querySelectorAll('.aba');
  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (b) {
        b.classList.remove('ativa');
        b.setAttribute('aria-selected', 'false');
      });
      document.querySelectorAll('.painel').forEach(function (p) {
        p.classList.remove('ativo');
      });
      aba.classList.add('ativa');
      aba.setAttribute('aria-selected', 'true');
      document.getElementById('painel-' + aba.dataset.aba).classList.add('ativo');
    });
  });

  function soDigitos(v) {
    return v.replace(/\D/g, '');
  }

  function formatarValor(v) {
    var d = soDigitos(v);
    if (!d) return '';
    var total = parseInt(d, 10);
    var reais = Math.floor(total / 100);
    var cents = total % 100;
    return 'R$ ' + reais.toLocaleString('pt-BR') + ',' + String(cents).padStart(2, '0');
  }

  function formatarCPF(v) {
    var d = soDigitos(v).slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + '.' + d.slice(3);
    return d;
  }

  function formatarCEP(v) {
    var d = soDigitos(v).slice(0, 8);
    if (d.length > 5) return d.slice(0, 5) + '-' + d.slice(5);
    return d;
  }

  function formatarData(v) {
    var d = soDigitos(v).slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + '/' + d.slice(2);
    return d;
  }

  function aoSair(nome, fn) {
    document.querySelectorAll('input[name="' + nome + '"]').forEach(function (i) {
      i.addEventListener('blur', function () {
        i.value = fn(i.value);
      });
    });
  }

  aoSair('valor', formatarValor);
  aoSair('cpf', formatarCPF);
  aoSair('cep', formatarCEP);
  aoSair('data_nascimento', formatarData);

  document.querySelectorAll('form.formulario').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      var dados = {};
      new FormData(form).forEach(function (v, k) {
        dados[k] = v;
      });
      dados.tipo = form.dataset.tipo;

      fetch('/api/solicitar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      })
        .then(function (r) { return r.json(); })
        .then(function (json) {
          var erros = form.querySelector('.erros');
          if (!json.ok) {
            erros.innerHTML = '';
            json.erros.forEach(function (msg) {
              var d = document.createElement('div');
              d.textContent = msg;
              erros.appendChild(d);
            });
            erros.hidden = false;
            return;
          }
          erros.hidden = true;
          document.getElementById('form-area').hidden = true;
          var conf = document.getElementById('confirmacao');
          conf.querySelector('.oficio').textContent = json.oficio;
          conf.hidden = false;
          window.scrollTo(0, 0);
        });
    });
  });
})();
