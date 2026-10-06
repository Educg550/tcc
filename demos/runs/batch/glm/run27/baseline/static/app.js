  // Abas
  const tabs = { alunos: document.getElementById('tab-alunos'), docentes: document.getElementById('tab-docentes') };
  const panels = { alunos: document.getElementById('form-alunos'), docentes: document.getElementById('form-docentes') };
  const errs = { alunos: document.getElementById('err-alunos'), docentes: document.getElementById('err-docentes') };

  function ativar(aba) {
    for (const k of ['alunos', 'docentes']) {
      tabs[k].classList.toggle('active', k === aba);
      panels[k].classList.toggle('active', k === aba);
    }
  }
  tabs.alunos.addEventListener('click', () => ativar('alunos'));
  tabs.docentes.addEventListener('click', () => ativar('docentes'));

  // Máscaras: aplicam na saída do campo (blur)
  function digitos(v) { return (v.match(/\d+/g) || []).join(''); }

  function moeda(v) {
    const d = digitos(v);
    if (!d) return '';
    const cents = d.slice(-2).padStart(2, '0');
    let reais = d.slice(0, -2) || '0';
    const grupos = [];
    while (reais.length > 3) { grupos.unshift(reais.slice(-3)); reais = reais.slice(0, -3); }
    grupos.unshift(reais);
    return 'R$ ' + grupos.join('.') + ',' + cents;
  }

  function cpf(v) {
    const d = digitos(v).slice(0, 11);
    return d.length === 11 ? d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4') : d;
  }

  function cep(v) {
    const d = digitos(v).slice(0, 8);
    return d.length === 8 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }

  function data(v) {
    const d = digitos(v).slice(0, 8);
    return d.length === 8 ? d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4) : d;
  }

  const mascaras = { moeda, cpf, cep, data };
  document.querySelectorAll('[data-mask]').forEach(el => {
    el.addEventListener('blur', () => {
      const m = el.dataset.mask;
      const f = mascaras[m](el.value);
      if (f !== el.value) el.value = f;
    });
  });

  // Envio
  async function enviar(form) {
    const aba = form.dataset.aba;
    const fd = new FormData(form);
    const body = {
      aba,
      valor_solicitado: parseInt(digitos(fd.get('valor')), 10) || 0,
      solicitante: {},
      evento: {},
      endereco: {},
      pagamento: {},
    };
    const grupos = { solicitante: ['nome', 'nusp', 'programa', 'nivel', 'tipo', 'email'],
                     evento: ['evento_nome', 'periodo', 'evento_cidade', 'evento_estado', 'evento_pais', 'evento_link', 'detalhamento', 'apresentacao'],
                     endereco: ['logradouro', 'numero', 'complemento', 'bairro', 'cep', 'cidade', 'estado', 'nascimento'],
                     pagamento: ['cpf', 'rg', 'banco', 'agencia', 'conta'] };
    const nomes = { evento_nome: 'nome', evento_cidade: 'cidade', evento_estado: 'estado', evento_pais: 'pais', evento_link: 'link' };
    for (const [g, campos] of Object.entries(grupos)) {
      for (const c of campos) {
        if (aba === 'docentes' && (c === 'nivel' || c === 'tipo')) continue;
        body[g][nomes[c] || c] = (fd.get(c) || '').toString().trim();
      }
    }
    const res = await fetch('/api/solicitar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const out = await res.json();
    errs[aba].innerHTML = '';
    if (out.mensagens && out.mensagens.length) {
      errs[aba].innerHTML = out.mensagens.map(m => `<div>${m}</div>`).join('');
      return;
    }
    document.getElementById('oficio').textContent = out.oficio;
    document.getElementById('confirmacao').classList.remove('hidden');
    document.querySelector('main').innerHTML = '';
    document.querySelector('main').appendChild(document.getElementById('confirmacao'));
  }

  for (const id of ['solic-alunos', 'solic-docentes']) {
    document.getElementById(id).addEventListener('submit', e => { e.preventDefault(); enviar(e.target); });
  }
