document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.tab').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var tab = this.dataset.tab;
      document.querySelectorAll('.tab').forEach(function(b) { b.classList.remove('active'); });
      document.querySelectorAll('.tab-content').forEach(function(f) { f.classList.remove('active'); });
      this.classList.add('active');
      document.getElementById('form-' + tab).classList.add('active');
    });
  });

  function formatarMoeda(valor) {
    var digits = valor.replace(/\D/g, '');
    if (!digits) return '';
    var num = parseInt(digits, 10);
    return 'R$ ' + (num / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function formatarCPF(valor) {
    var digits = valor.replace(/\D/g, '');
    if (!digits) return '';
    return digits.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
  }

  function formatarCEP(valor) {
    var digits = valor.replace(/\D/g, '');
    if (!digits) return '';
    return digits.replace(/(\d{5})(\d{3})/, '$1-$2');
  }

  function formatarData(valor) {
    var digits = valor.replace(/\D/g, '');
    if (!digits) return '';
    return digits.replace(/(\d{2})(\d{2})(\d{4})/, '$1/$2/$3');
  }

  function aplicarFormatacao(input) {
    var tipo = input.dataset.format;
    if (!tipo) return;
    var v = input.value;
    if (tipo === 'moeda') input.value = formatarMoeda(v);
    else if (tipo === 'cpf') input.value = formatarCPF(v);
    else if (tipo === 'cep') input.value = formatarCEP(v);
    else if (tipo === 'data') input.value = formatarData(v);
  }

  document.querySelectorAll('input[data-format]').forEach(function(input) {
    input.addEventListener('blur', function() { aplicarFormatacao(this); });
  });

  function extrairDados(form, aba) {
    var dados = { aba: aba };
    new FormData(form).forEach(function(value, key) { dados[key] = value; });
    return dados;
  }

  document.querySelectorAll('form.tab-content').forEach(function(form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      var aba = form.id === 'form-alunos' ? 'alunos' : 'docentes';
      var dados = extrairDados(form, aba);
      fetch('/solicitar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        var errosDiv = document.getElementById('erros-' + aba);
        if (data.erros) {
          errosDiv.innerHTML = data.erros.map(function(m) { return '<p>' + m + '</p>'; }).join('');
        } else {
          errosDiv.innerHTML = '';
          document.getElementById('formulario-container').style.display = 'none';
          var confirmacao = document.getElementById('confirmacao');
          confirmacao.style.display = 'block';
          document.getElementById('oficio').textContent = data.oficio;
        }
      });
    });
  });
});
