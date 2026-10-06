(function () {
  var abas = Array.prototype.slice.call(document.querySelectorAll('.aba'));
  var formularios = Array.prototype.slice.call(document.querySelectorAll('.formulario'));

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (b) { b.classList.toggle('ativa', b === aba); });
      formularios.forEach(function (f) { f.hidden = f.dataset.aba !== aba.dataset.aba; });
    });
  });

  function digitos(v) { return (v || '').replace(/\D/g, ''); }

  function formatarValor(v) {
    var d = digitos(v);
    if (!d) return '';
    d = d.replace(/^0+/, '') || '0';
    if (d.length < 3) d = d.padStart(3, '0');
    var centavos = d.slice(-2);
    var inteiros = d.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + inteiros + ',' + centavos;
  }

  function formatarCpf(v) {
    var d = digitos(v).slice(0, 11);
    return d
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
  }

  function formatarCep(v) {
    var d = digitos(v).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }

  function formatarData(v) {
    var d = digitos(v).slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
    return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  }

  document.addEventListener('focusout', function (e) {
    var el = e.target;
    if (!el || !el.dataset || !el.dataset.formato) return;
    switch (el.dataset.formato) {
      case 'valor': el.value = formatarValor(el.value); break;
      case 'cpf': el.value = formatarCpf(el.value); break;
      case 'cep': el.value = formatarCep(el.value); break;
      case 'data': el.value = formatarData(el.value); break;
    }
  });

  function mostrarErros(bloco, erros) {
    var caixa = bloco.querySelector('[data-erros]');
    caixa.innerHTML = '';
    erros.forEach(function (msg) {
      var p = document.createElement('p');
      p.textContent = msg;
      caixa.appendChild(p);
    });
  }

  function mostrarConfirmacao(oficio) {
    document.getElementById('oficio').textContent = oficio;
    document.getElementById('principal').hidden = true;
    document.getElementById('confirmacao').hidden = false;
  }

  formularios.forEach(function (bloco) {
    var form = bloco.querySelector('form');
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      fetch('/solicitar', { method: 'POST', body: new FormData(form) })
        .then(function (r) { return r.json(); })
        .then(function (dados) {
          if (dados.ok) {
            mostrarConfirmacao(dados.oficio);
          } else {
            mostrarErros(bloco, dados.erros);
            bloco.scrollIntoView({ block: 'nearest' });
          }
        });
    });
  });
})();
