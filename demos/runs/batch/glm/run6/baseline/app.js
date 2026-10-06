function soDigitos(t) { return (t || '').replace(/\D/g, ''); }

function fmtValor(c) {
  if (!c) return '';
  var t = String(Math.floor(c / 100)), grupos = [];
  while (t.length > 3) { grupos.unshift(t.slice(-3)); t = t.slice(0, -3); }
  grupos.unshift(t);
  return 'R$ ' + grupos.join('.') + ',' + String(c % 100).padStart(2, '0');
}

var formatadores = {
  valor: function (v) { return fmtValor(parseInt(soDigitos(v) || '0', 10)); },
  cpf: function (v) {
    var d = soDigitos(v).slice(0, 11);
    return d.length === 11 ? d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9) : d;
  },
  cep: function (v) {
    var d = soDigitos(v).slice(0, 8);
    return d.length === 8 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  },
  nascimento: function (v) {
    var d = soDigitos(v).slice(0, 8);
    return d.length === 8 ? d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4) : d;
  }
};

Object.keys(formatadores).forEach(function (nome) {
  document.querySelectorAll('[name=' + nome + ']').forEach(function (el) {
    el.addEventListener('blur', function () { el.value = formatadores[nome](el.value); });
  });
});

document.querySelectorAll('.tab').forEach(function (btn) {
  btn.addEventListener('click', function () {
    document.querySelectorAll('.tab').forEach(function (b) { b.classList.toggle('ativa', b === btn); });
    ['alunos', 'docentes'].forEach(function (k) {
      document.getElementById('form-' + k).hidden = (k !== btn.dataset.aba);
    });
  });
});

document.querySelectorAll('form.solicitacao').forEach(function (form) {
  form.addEventListener('submit', async function (ev) {
    ev.preventDefault();
    var fd = new FormData(form);
    var payload = { tipo: form.dataset.tipo };
    fd.forEach(function (v, k) { payload[k] = String(v).trim(); });
    payload.valor = parseInt(soDigitos(fd.get('valor')) || '0', 10);
    var r = await fetch('/api/solicitar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(function (resp) { return resp.json(); });
    var err = document.getElementById('erros-' + form.dataset.tipo);
    err.replaceChildren();
    if (r.erros && r.erros.length) {
      r.erros.forEach(function (e) {
        var d = document.createElement('div');
        d.textContent = e;
        err.appendChild(d);
      });
      err.hidden = false;
    } else {
      err.hidden = true;
      document.querySelector('main').hidden = true;
      document.getElementById('oficio').textContent = r.oficio;
      document.getElementById('confirmacao').hidden = false;
    }
  });
});
