document.addEventListener('DOMContentLoaded', function () {

  /* ---------- Troca de abas ---------- */
  var secoes = {
    alunos: document.getElementById('aba-alunos'),
    docentes: document.getElementById('aba-docentes')
  };
  var confirmacao = document.getElementById('confirmacao');

  document.querySelectorAll('.aba').forEach(function (btn) {
    btn.addEventListener('click', function () {
      secoes.alunos.hidden = btn.dataset.aba !== 'alunos';
      secoes.docentes.hidden = btn.dataset.aba !== 'docentes';
      confirmacao.hidden = true;
      document.querySelectorAll('.aba').forEach(function (b) {
        b.classList.toggle('ativa', b.dataset.aba === btn.dataset.aba);
      });
    });
  });

  /* ---------- Máscaras ---------- */
  function soDigitos(s) { return s.replace(/\D/g, ''); }

  function formatador(cls, fn) {
    document.querySelectorAll('.' + cls).forEach(function (el) {
      el.addEventListener('blur', function () {
        var dig = soDigitos(el.value);
        el.value = dig ? fn(dig) : '';
      });
    });
  }

  formatador('moeda', function (d) {
    var v = parseInt(d, 10) || 0;
    var int = String(Math.floor(v / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + int + ',' + String(v % 100).padStart(2, '0');
  });

  formatador('cpf', function (d) {
    var s = d.slice(0, 11);
    if (s.length > 9) return s.slice(0, 3) + '.' + s.slice(3, 6) + '.' + s.slice(6, 9) + '-' + s.slice(9);
    if (s.length > 6) return s.slice(0, 3) + '.' + s.slice(3, 6) + '.' + s.slice(6);
    if (s.length > 3) return s.slice(0, 3) + '.' + s.slice(3);
    return s;
  });

  formatador('cep', function (d) {
    var s = d.slice(0, 8);
    return s.length > 5 ? s.slice(0, 5) + '-' + s.slice(5) : s;
  });

  formatador('nasc', function (d) {
    var s = d.slice(0, 8);
    if (s.length > 4) return s.slice(0, 2) + '/' + s.slice(2, 4) + '/' + s.slice(4);
    if (s.length > 2) return s.slice(0, 2) + '/' + s.slice(2);
    return s;
  });

  /* ---------- Textareas com altura automática ---------- */
  document.querySelectorAll('textarea').forEach(function (ta) {
    function ajustar() {
      ta.style.height = 'auto';
      ta.style.height = ta.scrollHeight + 'px';
    }
    ta.addEventListener('input', ajustar);
    ajustar();
  });

  /* ---------- Coleta dos dados do formulário ---------- */
  function coletar(form) {
    var dados = {};
    form.querySelectorAll('input, select, textarea').forEach(function (el) {
      dados[el.name] = el.value.trim();
    });
    return dados;
  }

  /* ---------- Envio ---------- */
  function mostrarErros(ul, erros) {
    ul.innerHTML = '';
    erros.forEach(function (e) {
      var li = document.createElement('li');
      li.textContent = e;
      ul.appendChild(li);
    });
    ul.hidden = false;
  }

  function enviar(form, idAba, ul, formSection) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      ul.hidden = true;
      var dados = coletar(form);
      dados.aba = idAba;

      fetch('/api/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      })
      .then(function (r) { return r.json(); })
      .then(function (resp) {
        if (resp.ok) {
          formSection.hidden = true;
          document.getElementById('oficio').textContent = resp.oficio;
          confirmacao.hidden = false;
          window.scrollTo(0, 0);
        } else {
          mostrarErros(ul, resp.erros);
        }
      });
    });
  }

  enviar(
    document.getElementById('form-alunos'), 'alunos',
    document.getElementById('erros-alunos'), secoes.alunos
  );
  enviar(
    document.getElementById('form-docentes'), 'docentes',
    document.getElementById('erros-docentes'), secoes.docentes
  );
});
