(function () {
  'use strict';

  function maskValor(v) {
    var d = v.replace(/\D/g, '');
    if (!d) return '';
    d = d.replace(/^0+/, '') || '0';
    d = d.padStart(3, '0');
    var centavos = d.slice(-2);
    var reais = d.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + reais + ',' + centavos;
  }

  function maskCPF(v) {
    var d = v.replace(/\D/g, '').slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + '.' + d.slice(3);
    return d;
  }

  function maskCEP(v) {
    var d = v.replace(/\D/g, '').slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }

  function maskData(v) {
    var d = v.replace(/\D/g, '').slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + '/' + d.slice(2);
    return d;
  }

  var mascaras = { valor: maskValor, cpf: maskCPF, cep: maskCEP, data: maskData };

  function aplicarMascara(input) {
    var fn = mascaras[input.dataset.mask];
    if (fn) input.value = fn(input.value);
  }

  document.querySelectorAll('.aba').forEach(function (aba) {
    aba.addEventListener('click', function () {
      document.querySelectorAll('.aba').forEach(function (a) {
        a.classList.toggle('ativo', a === aba);
      });
      document.querySelectorAll('.form').forEach(function (f) {
        f.classList.toggle('ativo', f.dataset.tab === aba.dataset.tab);
      });
    });
  });

  document.querySelectorAll('[data-mask]').forEach(function (input) {
    input.addEventListener('blur', function () { aplicarMascara(input); });
  });

  document.querySelectorAll('form.form').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();

      form.querySelectorAll('[data-mask]').forEach(aplicarMascara);

      var dados = {};
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = String(valor).trim();
      });
      dados.tab = form.dataset.tab;

      fetch('/api/solicitar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      })
        .then(function (r) { return r.json(); })
        .then(function (res) {
          if (res.ok) {
            document.getElementById('app').style.display = 'none';
            document.getElementById('oficio').textContent = res.oficio;
            document.getElementById('confirmacao').style.display = 'block';
          } else {
            var box = form.querySelector('.erros');
            box.innerHTML = res.erros.map(function (m) {
              return '<p></p>';
            }).join('');
            Array.prototype.forEach.call(box.children, function (p, i) {
              p.textContent = res.erros[i];
            });
            box.style.display = 'block';
          }
        });
    });
  });
})();
