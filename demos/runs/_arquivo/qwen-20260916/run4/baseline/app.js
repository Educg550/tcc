(function () {
  var abaAtual = 'alunos';
  var app = document.getElementById('app');
  var painelRef = null;
  var formularioRef = null;

  function somenteDigitos(v) { return (v || '').replace(/\D/g, ''); }

  function formatarMoeda(v) {
    var d = somenteDigitos(v);
    if (!d) return '';
    var cents = parseInt(d, 10);
    var inteiro = Math.floor(cents / 100);
    var dec = cents % 100;
    var s = String(inteiro).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + s + ',' + String(dec).padStart(2, '0');
  }

  function formatarCPF(v) {
    var d = somenteDigitos(v).slice(0, 11);
    var out = d.slice(0, 3);
    if (d.length >= 4) out += '.' + d.slice(3, 6);
    if (d.length >= 7) out += '.' + d.slice(6, 9);
    if (d.length >= 10) out += '-' + d.slice(9, 11);
    return out;
  }

  function formatarCEP(v) {
    var d = somenteDigitos(v).slice(0, 8);
    if (d.length <= 5) return d;
    return d.slice(0, 5) + '-' + d.slice(5);
  }

  function formatarData(v) {
    var d = somenteDigitos(v).slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
    return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  }

  function coletar(form) {
    var dados = {};
    var elems = form.querySelectorAll('input[name], select[name], textarea[name]');
    elems.forEach(function (el) {
      var val = el.value || '';
      if (el.name === 'valor') val = somenteDigitos(val);
      dados[el.name] = val;
    });
    return dados;
  }

  function renderizarOficio(oficio) {
    var esc = function (s) {
      return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    };
    app.innerHTML =
      '<header class="header">' +
        '<img src="/assets/usp-logo.png" alt="Universidade de São Paulo" class="logo">' +
        '<div class="inst">' +
          '<span class="inst-nome">Universidade de São Paulo</span>' +
          '<span class="inst-sub">Instituto de Matemática e Estatística — Pós-Graduação</span>' +
        '</div>' +
      '</header>' +
      '<main><section class="confirmacao">' +
        '<h2>Solicitação registrada</h2>' +
        '<pre class="oficio">' + esc(oficio) + '</pre>' +
      '</section></main>';
  }

  async function enviar(ev) {
    ev.preventDefault();
    var form = ev.currentTarget;
    var errosBox = document.getElementById('erros');
    var dados = coletar(form);
    dados.aba = abaAtual;

    errosBox.classList.remove('mostra');
    errosBox.textContent = '';

    try {
      var resp = await fetch('/api/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      });
      var j = await resp.json();
      if (!j.ok) {
        errosBox.textContent = j.erros.join('\n');
        errosBox.classList.add('mostra');
        errosBox.scrollIntoView({ block: 'nearest' });
        return;
      }
      renderizarOficio(j.oficio);
    } catch (e) {
      errosBox.textContent = 'Falha ao comunicar com o servidor.';
      errosBox.classList.add('mostra');
    }
  }

  function ligarCampos(form) {
    var mapear = {
      valor: formatarMoeda,
      cpf: formatarCPF,
      cep: formatarCEP,
      nascimento: formatarData
    };
    Object.keys(mapear).forEach(function (nome) {
      var el = form.querySelector('[name="' + nome + '"]');
      if (el) el.addEventListener('blur', function () { el.value = mapear[nome](el.value); });
    });

    var ag = form.querySelector('[name="agencia"]');
    if (ag) ag.addEventListener('blur', function () { ag.value = somenteDigitos(ag.value); });

    var nusp = form.querySelector('[name="nusp"]');
    if (nusp) nusp.addEventListener('blur', function () { nusp.value = somenteDigitos(nusp.value); });
  }

  function trocarAba(nome) {
    abaAtual = nome;
    var painel = document.querySelector('.painel');
    if (!painel) return;
    painel.classList.toggle('aba-alunos', nome === 'alunos');
    painel.classList.toggle('aba-docentes', nome === 'docentes');
    document.querySelectorAll('.aba').forEach(function (b) {
      b.classList.toggle('ativa', b.dataset.aba === nome);
      b.setAttribute('aria-selected', String(b.dataset.aba === nome));
    });
  }

  function montar() {
    formularioRef.addEventListener('submit', enviar);
    painelRef = document.querySelector('.painel');
    painelRef.classList.add('aba-' + abaAtual);

    document.querySelectorAll('.aba').forEach(function (b) {
      b.addEventListener('click', function () { trocarAba(b.dataset.aba); });
    });

    trocarAba(abaAtual);
    ligarCampos(formularioRef);
  }

  document.addEventListener('DOMContentLoaded', function () {
    formularioRef = document.getElementById('formulario');
    if (formularioRef) montar();
  });
})();
