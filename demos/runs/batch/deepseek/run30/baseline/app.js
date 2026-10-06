(function () {
  'use strict';

  function soDigitos(v) { return v.replace(/\D/g, ''); }

  function formataValor(v) {
    var d = soDigitos(v);
    if (!d) return '';
    d = d.padStart(3, '0');
    var inteiro = d.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + inteiro + ',' + d.slice(-2);
  }

  function formataCpf(v) {
    var d = soDigitos(v).slice(0, 11);
    return d.replace(/(\d{3})(\d)/, '$1.$2')
            .replace(/(\d{3})(\d)/, '$1.$2')
            .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
  }

  function formataCep(v) {
    var d = soDigitos(v).slice(0, 8);
    return d.replace(/(\d{5})(\d)/, '$1-$2');
  }

  function formataData(v) {
    var d = soDigitos(v).slice(0, 8);
    return d.replace(/(\d{2})(\d)/, '$1/$2')
            .replace(/(\d{2})(\d)/, '$1/$2');
  }

  var formatadores = {
    valor: formataValor,
    cpf: formataCpf,
    cep: formataCep,
    data: formataData
  };

  document.querySelectorAll('[data-format]').forEach(function (campo) {
    campo.addEventListener('blur', function () {
      var f = formatadores[campo.dataset.format];
      if (f) campo.value = f(campo.value);
    });
  });

  document.querySelectorAll('.aba').forEach(function (botao) {
    botao.addEventListener('click', function () {
      document.querySelectorAll('.aba').forEach(function (b) {
        b.classList.remove('ativa');
      });
      document.querySelectorAll('.painel').forEach(function (p) {
        p.classList.remove('ativo');
      });
      botao.classList.add('ativa');
      document.getElementById('form-' + botao.dataset.aba).classList.add('ativo');
    });
  });

  document.querySelectorAll('.form-solicitacao').forEach(function (form) {
    form.addEventListener('submit', function (evento) {
      evento.preventDefault();

      var dados = {};
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = valor;
      });
      dados.tipo = form.dataset.tipo;

      fetch('/api/solicitar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      })
        .then(function (r) { return r.json(); })
        .then(function (r) {
          if (r.ok) {
            document.getElementById('app').hidden = true;
            document.getElementById('oficio').textContent = r.oficio;
            document.getElementById('confirmacao').hidden = false;
            window.scrollTo(0, 0);
          } else {
            var alvo = form.querySelector('.erros');
            alvo.textContent = '';
            r.erros.forEach(function (mensagem) {
              var linha = document.createElement('div');
              linha.textContent = mensagem;
              alvo.appendChild(linha);
            });
          }
        });
    });
  });
})();
