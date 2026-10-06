const aba = { alunos: document.getElementById('tab-alunos'), docentes: document.getElementById('tab-docentes') };
const forms = { alunos: document.getElementById('form-alunos'), docentes: document.getElementById('form-docentes') };
const erros = { alunos: document.getElementById('erros-alunos'), docentes: document.getElementById('erros-docentes') };
let atual = 'alunos';
function mostrar(quem) {
  atual = quem;
  for (const k of ['alunos','docentes']) {
    aba[k].classList.toggle('ativa', k === quem);
    forms[k].hidden = k !== quem;
  }
}
aba.alunos.addEventListener('click', () => mostrar('alunos'));
aba.docentes.addEventListener('click', () => mostrar('docentes'));
function digitos(v) { return (v.match(/\d/g) || []).join(''); }
function fmtValor(v) {
  const d = digitos(v); if (!d) return '';
  const cents = d.padStart(3, '0');
  const inteiro = cents.slice(0, -2), dd = cents.slice(-2);
  const partes = [];
  let r = inteiro;
  while (r.length > 3) { partes.unshift(r.slice(-3)); r = r.slice(0, -3); }
  partes.unshift(r);
  return 'R$ ' + partes.join('.') + ',' + dd;
}
function fmtCPF(v) { const d = digitos(v).slice(0, 11); return d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4'); }
function fmtCEP(v) { const d = digitos(v).slice(0, 8); return d.length > 5 ? d.slice(0,5) + '-' + d.slice(5) : d; }
function fmtData(v) { const d = digitos(v).slice(0, 8); let s = d.slice(0,2); if (d.length > 2) s += '/' + d.slice(2,4); if (d.length > 4) s += '/' + d.slice(4,8); return s; }
for (const form of [forms.alunos, forms.docentes]) {
  form.querySelector('[name=valor]').addEventListener('blur', e => { e.target.value = fmtValor(e.target.value); });
  form.querySelector('[name=cpf]').addEventListener('blur', e => { e.target.value = fmtCPF(e.target.value); });
  form.querySelector('[name=cep]').addEventListener('blur', e => { e.target.value = fmtCEP(e.target.value); });
  form.querySelector('[name=nascimento]').addEventListener('blur', e => { e.target.value = fmtData(e.target.value); });
  form.addEventListener('submit', async ev => {
    ev.preventDefault();
    const quem = form === forms.alunos ? 'alunos' : 'docentes';
    const data = Object.fromEntries(new FormData(form).entries());
    data.aba = quem;
    const resp = await fetch('/api/solicitacao', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data) });
    const out = await resp.json();
    if (out.erros) {
      erros[quem].innerHTML = out.erros.map(e => '<p>' + e + '</p>').join('');
      return;
    }
    document.getElementById('oficio').textContent = out.oficio;
    document.getElementById('confirmacao').hidden = false;
    forms.alunos.hidden = true;
    forms.docentes.hidden = true;
    document.querySelector('nav').hidden = true;
  });
}
