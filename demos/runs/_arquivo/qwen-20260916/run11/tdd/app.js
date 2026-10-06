document.addEventListener('DOMContentLoaded', function () {
  // Tab switching
  const tabsNav = document.querySelectorAll('.tab-btn');
  tabsNav.forEach(function (btn) {
    btn.addEventListener('click', function () {
      tabsNav.forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      const alvo = btn.getAttribute('data-tab');
      document.querySelectorAll('.tab-content').forEach(function (c) { c.classList.remove('active'); });
      document.getElementById('form-' + alvo).classList.add('active');
      document.getElementById('erros-container').classList.remove('visible');
      document.getElementById('erros-container').textContent = '';
      document.getElementById('tabs-container').classList.remove('hidden');
      document.getElementById('confirmacao').classList.add('hidden');
    });
  });

  // Formatting functions
  function formatarValor(el) {
    const digitos = el.value.replace(/\D/g, '');
    if (!digitos) return;
    const centavos = parseInt(digitos, 10);
    const valor = (centavos / 100).toFixed(2);
    const partes = valor.split('.');
    partes[0] = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    el.value = 'R$ ' + partes[0] + ',' + partes[1];
  }

  function formatarCPF(el) {
    const d = el.value.replace(/\D/g, '').slice(0, 11);
    let r = d;
    if (d.length > 9) r = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9, 11);
    else if (d.length > 6) r = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    else if (d.length > 3) r = d.slice(0, 3) + '.' + d.slice(3);
    el.value = r;
  }

  function formatarCEP(el) {
    const d = el.value.replace(/\D/g, '').slice(0, 8);
    if (d.length > 5) el.value = d.slice(0, 5) + '-' + d.slice(5);
    else el.value = d;
  }

  function formatarData(el) {
    const d = el.value.replace(/\D/g, '').slice(0, 8);
    let r = d;
    if (d.length > 4) r = d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    else if (d.length > 2) r = d.slice(0, 2) + '/' + d.slice(2);
    el.value = r;
  }

  // Attach blur handlers to all formatable fields in both forms
  const camposFormataveis = [
    { selector: 'input[name="valor"]', fn: formatarValor },
    { selector: 'input[name="cpf"]', fn: formatarCPF },
    { selector: 'input[name="cep"]', fn: formatarCEP },
    { selector: 'input[name="data_nascimento"]', fn: formatarData },
  ];

  camposFormataveis.forEach(function (cfg) {
    document.querySelectorAll(cfg.selector).forEach(function (el) {
      el.addEventListener('blur', function () { cfg.fn(el); });
    });
  });

  // Form submission
  document.getElementById('form-alunos').addEventListener('submit', function (e) {
    e.preventDefault();
    enviarFormulario('/solicitacoes/alunos', e.target, false);
  });

  document.getElementById('form-docentes').addEventListener('submit', function (e) {
    e.preventDefault();
    enviarFormulario('/solicitacoes/docentes', e.target, true);
  });

  function coletarDados(form) {
    const dados = {};
    form.querySelectorAll('input, select, textarea').forEach(function (el) {
      if (el.name) {
        let val = el.value;
        if (el.name === 'valor') {
          const digitos = val.replace(/\D/g, '');
          val = digitos ? parseInt(digitos, 10) : 0;
        }
        dados[el.name] = val;
      }
    });
    return dados;
  }

  function enviarFormulario(url, form, docente) {
    const dados = coletarDados(form);
    if (docente) {
      delete dados.nivel;
      delete dados.tipo_auxilio;
    }

    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    })
      .then(function (resp) { return resp.json().then(function (data) { return { status: resp.status, data: data }; }); })
      .then(function (resultado) {
        if (resultado.status === 200 && resultado.data.oficio) {
          document.getElementById('tabs-container').classList.add('hidden');
          document.getElementById('confirmacao').classList.remove('hidden');
          document.getElementById('confirmacao').querySelector('h2').textContent = resultado.data.titulo;
          document.getElementById('oficio-texto').textContent = resultado.data.oficio;
        } else {
          const errosEl = document.getElementById('erros-container');
          errosEl.classList.add('visible');
          errosEl.textContent = '';
          (resultado.data.erros || []).forEach(function (msg) {
            errosEl.appendChild(document.createTextNode(msg));
            errosEl.appendChild(document.createElement('br'));
          });
        }
      })
      .catch(function () {
        const errosEl = document.getElementById('erros-container');
        errosEl.classList.add('visible');
        errosEl.textContent = 'Erro ao enviar solicitação.';
      });
  }
});
