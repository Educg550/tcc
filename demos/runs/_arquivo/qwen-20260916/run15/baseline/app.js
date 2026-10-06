(function () {
  'use strict';

  var abas = document.querySelectorAll('.aba');

  abas.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var alvo = btn.dataset.aba;
      abas.forEach(function (b) {
        var ativo = b === btn;
        b.classList.toggle('ativa', ativo);
        b.setAttribute('aria-selected', ativo ? 'true' : 'false');
        var painel = painelDe(b.dataset.aba);
        painel.classList.toggle('escondido', !ativo);
        painel.hidden = !ativo;
      });
      esconderConfirmacao();
      document.getElementById('topo').classList.remove('escondido');
      document.querySelector('main').classList.remove('escondido');
      mostrarPainel(alvo);
    });
  });

  function painelDe(aba) {
    return aba === 'ALUNOS' ? formAlunos : formDocentes;
  }

  function mostrarPainel(aba) {
    var painel = painelDe(aba);
    painel.classList.remove('escondido');
    painel.hidden = false;
  }

  var formAlunos = document.getElementById('form-alunos');
  var formDocentes = document.getElementById('form-docentes');
  var confirmacao = document.getElementById('confirmacao');
  var app = document.querySelector('main');
  var oficioEl = document.getElementById('oficio');

  [[formAlunos, 'ALUNOS'], [formDocentes, 'DOCENTES']].forEach(function (par) {
    var form = par[0], aba = par[1];
    form.addEventListener('submit', function (e) { e.preventDefault(); enviar(form, aba); });
    form.addEventListener('blur', onBlur, true);
  });

  function onBlur(e) {
    var el = e.target;
    if (!el.dataset) return;
    var tipo = el.dataset.formata;
    if (!tipo) return;
    var somenteDigitos = el.value.replace(/\D/g, '');
    if (somenteDigitos === '') { el.value = ''; return; }
    if (tipo === 'cpf') {
      var c = somenteDigitos.slice(0, 11);
      var r = c.slice(0, 3);
      if (c.length >= 4) r += '.' + c.slice(3, 6);
      if (c.length >= 7) r += '.' + c.slice(6, 9);
      if (c.length >= 10) r += '-' + c.slice(9, 11);
      el.value = r;
    } else if (tipo === 'cep') {
      var z = somenteDigitos.slice(0, 8);
      el.value = z.length >= 6 ? z.slice(0, 5) + '-' + z.slice(5) : z;
    } else if (tipo === 'data') {
      var d = somenteDigitos.slice(0, 8);
      var s = d.slice(0, 2);
      if (d.length >= 3) s += '/' + d.slice(2, 4);
      if (d.length >= 5) s += '/' + d.slice(4, 8);
      el.value = s;
    } else if (tipo === 'moeda') {
      el.value = formatarMoeda(parseInt(somenteDigitos, 10) || 0);
    }
  }

  function formatarMoeda(centavos) {
    var inteiro = Math.floor(centavos / 100);
    var frac = String(centavos % 100).padStart(2, '0');
    var s = '', n = String(inteiro);
    while (n.length > 3) { s = '.' + n.slice(-3) + s; n = n.slice(0, -3); }
    return 'R$ ' + n + s + ',' + frac;
  }

  function coletar(form) {
    var dados = {};
    form.querySelectorAll('[name]').forEach(function (el) {
      dados[el.name] = el.value.trim();
    });
    return dados;
  }

  function enviar(form, aba) {
    var dados = coletar(form);
    fetch('/solicitacao?aba=' + encodeURIComponent(aba), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados)
    })
      .then(function (r) { return r.json(); })
      .then(function (resp) {
        var caixa = document.getElementById('erros-' + (aba === 'ALUNOS' ? 'alunos' : 'docentes'));
        if (resp.ok) {
          caixa.innerHTML = '';
          mostrarConfirmacao(resp.oficio);
        } else {
          caixa.innerHTML = '';
          resp.erros.forEach(function (m) {
            var p = document.createElement('p');
            p.textContent = m;
            caixa.appendChild(p);
          });
        }
      })
      .catch(function () {
        var caixa = document.getElementById('erros-' + (aba === 'ALUNOS' ? 'alunos' : 'docentes'));
        var p = document.createElement('p');
        p.textContent = 'Erro ao processar a solicitação';
        caixa.innerHTML = '';
        caixa.appendChild(p);
      });
  }

  function mostrarConfirmacao(texto) {
    document.querySelector('main').classList.add('escondido');
    document.getElementById('topo').classList.remove('escondido');
    confirmacao.classList.remove('escondido');
    confirmacao.hidden = false;
    oficioEl.textContent = texto;
  }

  function esconderConfirmacao() {
    confirmacao.classList.add('escondido');
    confirmacao.hidden = true;
    document.querySelector('main').classList.remove('escondido');
  }
})();
