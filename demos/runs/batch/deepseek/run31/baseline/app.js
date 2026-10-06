(function () {
  var abas = document.querySelectorAll('.aba');
  var paineis = document.querySelectorAll('.painel');

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (a) { a.classList.toggle('ativa', a === aba); });
      paineis.forEach(function (p) {
        p.classList.toggle('ativo', p.id === 'painel-' + aba.dataset.aba);
      });
    });
  });

  document.querySelectorAll('input[data-mask]').forEach(function (inp) {
    inp.addEventListener('blur', function () { aplicar(inp); });
  });

  document.querySelectorAll('.formulario').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      enviar(form);
    });
  });

  function soDigitos(v) { return v.replace(/\D/g, ''); }

  function aplicar(inp) {
    var d = soDigitos(inp.value);
    if (!d) { return; }
    switch (inp.dataset.mask) {
      case 'valor': inp.value = 'R$ ' + moeda(d); break;
      case 'cpf': inp.value = cpf(d); break;
      case 'cep': inp.value = cep(d); break;
      case 'data': inp.value = data(d); break;
    }
  }

  function moeda(d) {
    var n = d.padStart(3, '0');
    var centavos = n.slice(-2);
    var reais = n.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return reais + ',' + centavos;
  }

  function cpf(d) {
    d = d.slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + '.' + d.slice(3);
    return d;
  }

  function cep(d) {
    d = d.slice(0, 8);
    if (d.length > 5) return d.slice(0, 5) + '-' + d.slice(5);
    return d;
  }

  function data(d) {
    d = d.slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + '/' + d.slice(2);
    return d;
  }

  async function enviar(form) {
    var errosBox = form.querySelector('.erros');
    errosBox.innerHTML = '';

    var dados = { tipo: form.dataset.tipo };
    form.querySelectorAll('[name]').forEach(function (el) {
      dados[el.name] = el.value.trim();
    });

    var resp = await fetch('/api/solicitar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados)
    });
    var resultado = await resp.json();

    if (resultado.erros) {
      resultado.erros.forEach(function (msg) {
        var div = document.createElement('div');
        div.textContent = msg;
        errosBox.appendChild(div);
      });
      return;
    }

    document.getElementById('app').classList.add('oculto');
    document.getElementById('confirmacao').classList.remove('oculto');
    document.getElementById('oficio').textContent = resultado.oficio;
  }
})();
