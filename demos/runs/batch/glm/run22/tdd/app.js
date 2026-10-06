function switchTab(tab) {
  document.getElementById('tab-alunos').classList.toggle('active', tab === 'alunos');
  document.getElementById('tab-docentes').classList.toggle('active', tab === 'docentes');
  document.getElementById('form-alunos').classList.toggle('hidden', tab !== 'alunos');
  document.getElementById('form-docentes').classList.toggle('hidden', tab !== 'docentes');
}

function formatarMoeda(el) {
  var d = el.value.replace(/\D/g, '');
  if (d === '') { el.value = ''; return; }
  var cents = parseInt(d, 10);
  var reais = Math.floor(cents / 100);
  var c = String(cents % 100).padStart(2, '0');
  var r = reais.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  el.value = 'R$ ' + r + ',' + c;
}

function formatarCpf(el) {
  var d = el.value.replace(/\D/g, '').slice(0, 11);
  el.value = d.length === 11 ? d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4') : d;
}

function formatarCep(el) {
  var d = el.value.replace(/\D/g, '').slice(0, 8);
  el.value = d.length === 8 ? d.replace(/(\d{5})(\d{3})/, '$1-$2') : d;
}

function formatarData(el) {
  var d = el.value.replace(/\D/g, '').slice(0, 8);
  el.value = d.length === 8 ? d.replace(/(\d{2})(\d{2})(\d{4})/, '$1/$2/$3') : d;
}

async function submitForm(e, aba) {
  e.preventDefault();
  var form = e.target;
  var data = {};
  new FormData(form).forEach(function (v, k) { data[k] = v; });
  data.aba = aba;
  var res = await fetch('/api/solicitar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  var json = await res.json();
  var erros = document.getElementById('errors-' + aba);
  erros.innerHTML = '';
  if (json.ok) {
    document.getElementById('page-form').classList.add('hidden');
    document.getElementById('confirm-title').textContent = 'Solicitação registrada';
    document.getElementById('oficio').textContent = json.oficio;
    document.getElementById('page-confirm').classList.remove('hidden');
  } else {
    json.erros.forEach(function (m) {
      var div = document.createElement('div');
      div.textContent = m;
      erros.appendChild(div);
    });
  }
  return false;
}