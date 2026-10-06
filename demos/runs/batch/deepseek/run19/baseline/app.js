const abas = document.querySelectorAll('.aba');
const formularios = document.querySelectorAll('.formulario');

function selecionarAba(nome) {
  abas.forEach(b => b.classList.toggle('ativa', b.dataset.aba === nome));
  formularios.forEach(f => f.classList.toggle('ativo', f.dataset.aba === nome));
}

abas.forEach(b => b.addEventListener('click', () => selecionarAba(b.dataset.aba)));

function formataReais(n) {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

function formataMoeda(el) {
  const d = el.value.replace(/\D/g, '');
  if (!d) {
    el.value = '';
    return;
  }
  const centavos = parseInt(d, 10);
  const reais = Math.floor(centavos / 100);
  const resto = String(centavos % 100).padStart(2, '0');
  el.value = 'R$ ' + formataReais(reais) + ',' + resto;
}

function formataCpf(el) {
  const d = el.value.replace(/\D/g, '').slice(0, 11);
  if (d.length > 9) {
    el.value = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  } else if (d.length > 6) {
    el.value = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
  } else if (d.length > 3) {
    el.value = d.slice(0, 3) + '.' + d.slice(3);
  } else {
    el.value = d;
  }
}

function formataCep(el) {
  const d = el.value.replace(/\D/g, '').slice(0, 8);
  el.value = d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formataData(el) {
  const d = el.value.replace(/\D/g, '').slice(0, 8);
  if (d.length > 4) {
    el.value = d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  } else if (d.length > 2) {
    el.value = d.slice(0, 2) + '/' + d.slice(2);
  } else {
    el.value = d;
  }
}

const formatadores = { moeda: formataMoeda, cpf: formataCpf, cep: formataCep, data: formataData };

document.querySelectorAll('[data-format]').forEach(el => {
  el.addEventListener('blur', () => formatadores[el.dataset.format](el));
});

formularios.forEach(form => {
  form.addEventListener('submit', async evento => {
    evento.preventDefault();

    const campos = {};
    form.querySelectorAll('[name]').forEach(el => { campos[el.name] = el.value; });

    const resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ aba: form.dataset.aba, campos: campos })
    });
    const dados = await resposta.json();

    const caixaErros = form.querySelector('.erros');

    if (dados.erros) {
      caixaErros.textContent = dados.erros.join('\n');
      caixaErros.classList.add('visivel');
      return;
    }

    caixaErros.classList.remove('visivel');
    document.getElementById('abainterface').style.display = 'none';
    document.getElementById('oficio').textContent = dados.oficio;
    document.getElementById('confirmacao').classList.add('ativo');
  });
});
