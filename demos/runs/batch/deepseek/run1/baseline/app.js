document.addEventListener('DOMContentLoaded', () => {
  const abas = document.querySelectorAll('.aba');
  const forms = {
    alunos: document.getElementById('form-alunos'),
    docentes: document.getElementById('form-docentes'),
  };
  const confirmacao = document.getElementById('confirmacao');
  const oficioEl = document.getElementById('oficio');
  let abaAtiva = 'alunos';

  function mostrarAba(nome) {
    abaAtiva = nome;
    abas.forEach(b => b.classList.toggle('ativa', b.dataset.aba === nome));
    Object.entries(forms).forEach(([key, form]) => {
      form.classList.toggle('oculto', key !== nome);
    });
    confirmacao.classList.add('oculto');
  }

  abas.forEach(b => b.addEventListener('click', () => mostrarAba(b.dataset.aba)));

  function formatarMoeda(input) {
    const digitos = input.value.replace(/\D/g, '');
    if (!digitos) { input.value = ''; return; }
    const n = parseInt(digitos, 10);
    const centavos = n % 100;
    const reais = Math.floor(n / 100);
    const reaisStr = reais.toLocaleString('pt-BR');
    input.value = `R$ ${reaisStr},${String(centavos).padStart(2, '0')}`;
  }

  function formatarCPF(input) {
    const d = input.value.replace(/\D/g, '').slice(0, 11);
    let v = d;
    if (d.length > 9) v = `${d.slice(0,3)}.${d.slice(3,6)}.${d.slice(6,9)}-${d.slice(9)}`;
    else if (d.length > 6) v = `${d.slice(0,3)}.${d.slice(3,6)}.${d.slice(6)}`;
    else if (d.length > 3) v = `${d.slice(0,3)}.${d.slice(3)}`;
    input.value = v;
  }

  function formatarCEP(input) {
    const d = input.value.replace(/\D/g, '').slice(0, 8);
    input.value = d.length > 5 ? `${d.slice(0,5)}-${d.slice(5)}` : d;
  }

  function formatarData(input) {
    const d = input.value.replace(/\D/g, '').slice(0, 8);
    let v = d;
    if (d.length > 4) v = `${d.slice(0,2)}/${d.slice(2,4)}/${d.slice(4)}`;
    else if (d.length > 2) v = `${d.slice(0,2)}/${d.slice(2)}`;
    input.value = v;
  }

  document.querySelectorAll('.formata-moeda').forEach(inp =>
    inp.addEventListener('blur', () => formatarMoeda(inp)));
  document.querySelectorAll('.formata-cpf').forEach(inp =>
    inp.addEventListener('blur', () => formatarCPF(inp)));
  document.querySelectorAll('.formata-cep').forEach(inp =>
    inp.addEventListener('blur', () => formatarCEP(inp)));
  document.querySelectorAll('.formata-data').forEach(inp =>
    inp.addEventListener('blur', () => formatarData(inp)));

  Object.entries(forms).forEach(([nome, form]) => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const errosDiv = form.querySelector('.erros');
      errosDiv.textContent = '';
      const dados = {};
      new FormData(form).forEach((val, key) => { dados[key] = val; });
      try {
        const resp = await fetch('/solicitar', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(dados),
        });
        const json = await resp.json();
        if (json.erros) {
          errosDiv.textContent = json.erros.join('\n');
        } else if (json.oficio) {
          oficioEl.textContent = json.oficio;
          form.classList.add('oculto');
          document.querySelector('.abas').classList.add('oculto');
          confirmacao.classList.remove('oculto');
        }
      } catch (err) {
        errosDiv.textContent = 'Erro ao enviar solicitação.';
      }
    });
  });
});