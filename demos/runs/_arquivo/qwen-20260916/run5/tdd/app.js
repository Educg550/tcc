document.addEventListener('DOMContentLoaded', () => {

  const tabs = document.querySelectorAll('.tab-btn');
  const contents = document.querySelectorAll('.tab-content');
  const confirmEl = document.getElementById('confirmacao');
  const container = document.querySelector('.container');

  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      tabs.forEach(t => t.classList.toggle('active', t === btn));
      contents.forEach(c => {
        c.classList.toggle('hidden', c.dataset.content !== tab);
      });
      confirmEl.classList.add('hidden');
      contents.forEach(c => {
        if (!c.classList.contains('hidden')) {
          c.style.display = '';
        }
      });
    });
  });

  function formatCurrency(v) {
    const d = v.replace(/\D/g, '');
    if (!d) return '';
    const n = parseInt(d, 10) / 100;
    return 'R$ ' + n.toFixed(2).replace(/\./, ',').replace(/\B(?=(\d{3})+(?!\d))/g, ',').replace(/(?<=\d),(?=\d{2})/, '.');
  }

  function formatCurrency(v) {
    const d = v.replace(/\D/g, '');
    if (!d) return '';
    const cents = parseInt(d, 10);
    const real = Math.floor(cents / 100);
    const cent = cents % 100;
    const rStr = real.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    const cStr = cent.toString().padStart(2, '0');
    return 'R$ ' + rStr + ',' + cStr;
  }

  function formatCPF(v) {
    const d = v.replace(/\D/g, '').substring(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.substring(0, 3) + '.' + d.substring(3);
    if (d.length <= 9) return d.substring(0, 3) + '.' + d.substring(3, 6) + '.' + d.substring(6);
    return d.substring(0, 3) + '.' + d.substring(3, 6) + '.' + d.substring(6, 9) + '-' + d.substring(9);
  }

  function formatCEP(v) {
    const d = v.replace(/\D/g, '').substring(0, 8);
    if (d.length <= 5) return d;
    return d.substring(0, 5) + '-' + d.substring(5);
  }

  function formatDate(v) {
    const d = v.replace(/\D/g, '').substring(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.substring(0, 2) + '/' + d.substring(2);
    return d.substring(0, 2) + '/' + d.substring(2, 4) + '/' + d.substring(4);
  }

  document.querySelectorAll('input[name="valor_solicitado"]').forEach(el => {
    el.addEventListener('blur', () => {
      el.value = formatCurrency(el.value);
    });
  });

  document.querySelectorAll('input[name="cpf"]').forEach(el => {
    el.addEventListener('blur', () => {
      el.value = formatCPF(el.value);
    });
  });

  document.querySelectorAll('input[name="cep"]').forEach(el => {
    el.addEventListener('blur', () => {
      el.value = formatCEP(el.value);
    });
  });

  document.querySelectorAll('input[name="data_nascimento"]').forEach(el => {
    el.addEventListener('blur', () => {
      el.value = formatDate(el.value);
    });
  });

  function getData(aba) {
    const prefix = aba === 'alunos' ? 'al_' : 'do_';
    const get = (name) => {
      const el = document.querySelector(`[name="${name}"]`);
      return el ? el.value.trim() : '';
    };

    const data = {
      aba: aba,
      nome_completo: get('nome_completo'),
      n_usp: get('n_usp'),
      programa: get('programa'),
      email: get('email'),
      nome_evento: get('nome_evento'),
      periodo_evento: get('periodo_evento'),
      cidade_evento: get('cidade_evento'),
      estado_evento: get('estado_evento'),
      pais_evento: get('pais_evento'),
      link_evento: get('link_evento'),
      valor_solicitado: get('valor_solicitado'),
      detalhamento: get('detalhamento'),
      apresentacao: get('apresentacao'),
      data_nascimento: get('data_nascimento'),
      logradouro: get('logradouro'),
      numero: get('numero'),
      complemento: get('complemento'),
      bairro: get('bairro'),
      cep: get('cep'),
      cidade: get('cidade'),
      estado: get('estado'),
      cpf: get('cpf'),
      rg: get('rg'),
      banco: get('banco'),
      agencia: get('agencia'),
      conta: get('conta'),
    };

    if (aba === 'alunos') {
      data.nivel = get('nivel');
      data.tipo_auxilio = get('tipo_auxilio');
    }

    return data;
  }

  function showErrors(aba, erros) {
    const box = document.getElementById('erros-' + aba);
    box.textContent = erros.join('\n');
  }

  function clearErrors() {
    document.querySelectorAll('.erros-box').forEach(b => b.textContent = '');
  }

  function showOficio(t) {
    contents.forEach(c => c.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    confirmEl.classList.remove('hidden');
    document.getElementById('oficio-texto').textContent = t;
  }

  async function submitForm(aba, form) {
    const data = getData(aba);
    const res = await fetch('/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (res.status === 400) {
      const body = await res.json();
      showErrors(aba, body.erros);
      return;
    }

    const body = await res.json();
    clearErrors();
    showOficio(body.oficio);
  }

  document.getElementById('form-alunos').addEventListener('submit', (e) => {
    e.preventDefault();
    submitForm('alunos', e.target);
  });

  document.getElementById('form-docentes').addEventListener('submit', (e) => {
    e.preventDefault();
    submitForm('docentes', e.target);
  });

});