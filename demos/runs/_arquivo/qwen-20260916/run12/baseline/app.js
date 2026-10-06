// ---------- Tabs ----------
const tabs = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.tab-panel');
let abaAtiva = 'alunos';

tabs.forEach(t => {
  t.addEventListener('click', () => {
    tabs.forEach(x => { x.classList.remove('active'); x.setAttribute('aria-selected', 'false'); });
    panels.forEach(p => p.classList.remove('active'));
    t.classList.add('active');
    t.setAttribute('aria-selected', 'true');
    abaAtiva = t.dataset.tab;
    document.querySelector(`.tab-panel[data-tab="${abaAtiva}"]`).classList.add('active');
    limparErros();
  });
});

// ---------- Formatting on blur ----------
function formatValor(v) {
  const dig = v.replace(/\D/g, '');
  if (!dig) return '';
  const centavos = parseInt(dig, 10);
  const inteiro = Math.floor(centavos / 100);
  const frac = centavos % 100;
  const inteiroStr = String(inteiro).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `R$ ${inteiroStr},${String(frac).padStart(2, '0')}`;
}

function formatCPF(v) {
  const d = v.replace(/\D/g, '').slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return d.slice(0, 3) + '.' + d.slice(3);
  if (d.length <= 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
  return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
}

function formatCEP(v) {
  const d = v.replace(/\D/g, '').slice(0, 8);
  if (d.length <= 5) return d;
  return d.slice(0, 5) + '-' + d.slice(5);
}

function formatData(v) {
  const d = v.replace(/\D/g, '').slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
  return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
}

const FORMATADORES = { valor: formatValor, cpf: formatCPF, cep: formatCEP, data: formatData };

document.querySelectorAll('[data-format]').forEach(input => {
  input.addEventListener('blur', () => {
    const tipo = input.dataset.format;
    if (FORMATADORES[tipo]) input.value = FORMATADORES[tipo](input.value);
  });
});

// ---------- Errors ----------
function limparErros() {
  document.querySelectorAll('.errors').forEach(e => { e.textContent = ''; });
}

// ---------- Submit ----------
document.querySelectorAll('[data-submit]').forEach(btn => {
  btn.addEventListener('click', () => {
    const aba = btn.dataset.submit;
    const panel = document.querySelector(`.tab-panel[data-tab="${aba}"]`);
    const dados = { _aba: aba };
    panel.querySelectorAll('[data-field]').forEach(el => {
      let v = el.value.trim();
      if (el.dataset.format === 'valor' && v) {
        const d = v.replace(/\D/g, '');
        if (d) v = String(parseInt(d, 10));
      }
      dados[el.dataset.field] = v;
    });
    const errorBox = panel.parentElement.querySelector('.errors');
    fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados)
    })
    .then(r => r.json())
    .then(res => {
      if (!res.ok) {
        errorBox.textContent = res.erros.join('\n');
        return;
      }
      document.getElementById('oficio').textContent = res.oficio;
      document.getElementById('page-form').classList.add('hidden');
      document.getElementById('page-confirm').classList.remove('hidden');
    });
  });
});
