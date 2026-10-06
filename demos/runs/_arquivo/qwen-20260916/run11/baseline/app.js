(function () {
  'use strict';

  var abas = document.querySelectorAll('.aba');
  var paineis = { alunos: document.getElementById('painel-alunos'), docentes: document.getElementById('painel-docentes') };
  var formulario = document.getElementById('conteudo-form');
  var confirmacao = document.getElementById('conteudo-confirmacao');

  abas.forEach(function (btn) {
    btn.addEventListener('click', function () {
      abas.forEach(function (b) { b.classList.remove('ativa'); b.setAttribute('aria-selected', 'false'); });
      Object.keys(paineis).forEach(function (k) { paineis[k].hidden = true; });
      btn.classList.add('ativa');
      btn.setAttribute('aria-selected', 'true');
      paineis[btn.dataset.aba].hidden = false;
      formulario.hidden = false;
      confirmacao.hidden = true;
    });
  });

  function digitos(s) { return s.replace(/\D/g, ''); }

  function formatarMoeda(s) {
    var d = digitos(s).slice(0, 12);
    while (d.length < 3) d = '0' + d;
    var inteiros = d.slice(0, -2) || '0';
    var centavos = d.slice(-2);
    inteiros = inteiros.replace(/^0+(?=\d)/, '');
    return 'R$ ' + inteiros.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + centavos;
  }

  function formatarCpf(s) {
    var d = digitos(s).slice(0, 11);
    return d.replace(/(\d{3})(\d{0,3})(\d{0,3})(\d{0,2})/, function (m, a, b, c, e) {
      return a + (b ? '.' + b : '') + (c ? '.' + c : '') + (e ? '-' + e : '');
    });
  }

  function formatarCep(s) {
    var d = digitos(s).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }

  function formatarData(s) {
    var d = digitos(s).slice(0, 8);
    return d.replace(/(\d{2})(\d{0,2})(\d{0,4})/, function (m, a, b, c) {
      return a + (b ? '/' + b : '') + (c ? '/' + c : '');
    });
  }

  var formatadores = {
    'formata-valor': formatarMoeda,
    'formata-cpf': formatarCpf,
    'formata-cep': formatarCep,
    'formata-data': formatarData
  };

  document.querySelectorAll('input[class*="formata-"]').forEach(function (campo) {
    Object.keys(formatadores).forEach(function (cls) {
      if (campo.classList.contains(cls)) {
        campo.addEventListener('blur', function () {
          if (campo.value !== '') campo.value = formatadores[cls](campo.value);
        });
      }
    });
  });

  document.querySelectorAll('form[data-form]').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var aba = form.dataset.form;
      var dados = {};
      Array.prototype.forEach.call(form.elements, function (el) {
        if (el.name) dados[el.name] = el.value;
      });
      fetch('/api/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ aba: aba, dados: dados })
      }).then(function (r) { return r.json(); }).then(function (resp) {
        var caixa = form.querySelector('.erros');
        if (resp.ok) {
          caixa.textContent = '';
          document.getElementById('oficio').textContent = resp.oficio;
          formulario.hidden = true;
          confirmacao.hidden = false;
        } else {
          caixa.innerHTML = '';
          (resp.erros || []).forEach(function (e) {
            var linha = document.createElement('div');
            linha.textContent = e;
            caixa.appendChild(linha);
          });
        }
      });
    });
  });
})();
