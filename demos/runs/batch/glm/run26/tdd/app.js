const API_BASE = 'http://localhost:8000';

function switchTab(tab) {
  document.getElementById('tab-aluno').classList.toggle('active', tab === 'aluno');
  document.getElementById('tab-docente').classList.toggle('active', tab === 'docente');
  document.getElementById('tab-content-aluno').classList.toggle('active', tab === 'aluno');
  document.getElementById('tab-content-docente').classList.toggle('active', tab === 'docente');
}

document.getElementById('tab-aluno').addEventListener('click', () => switchTab('aluno'));
document.getElementById('tab-docente').addEventListener('click', () => switchTab('docente'));

function formatCEP(input) {
  let v = input.value.replace(/\D/g, '').substring(0, 8);
  if (v.length > 5) {
    input.value = v.substring(0, 5) + '-' + v.substring(5);
  } else {
    input.value = v;
  }
}

function formatCPF(input) {
  let v = input.value.replace(/\D/g, '').substring(0, 11);
  if (v.length > 9) {
    input.value = v.substring(0, 3) + '.' + v.substring(3, 6) + '.' + v.substring(6, 9) + '-' + v.substring(9);
  } else if (v.length > 6) {
    input.value = v.substring(0, 3) + '.' + v.substring(3, 6) + '.' + v.substring(6);
  } else if (v.length > 3) {
    input.value = v.substring(0, 3) + '.' + v.substring(3);
  } else {
    input.value = v;
  }
}

function formatDate(input) {
  let v = input.value.replace(/\D/g, '').substring(0, 8);
  if (v.length > 4) {
    input.value = v.substring(0, 2) + '/' + v.substring(2, 4) + '/' + v.substring(4);
  } else if (v.length > 2) {
    input.value = v.substring(0, 2) + '/' + v.substring(2);
  } else {
    input.value = v;
  }
}

function formatCurrency(input) {
  let v = input.value.replace(/\D/g, '');
  if (!v) { input.value = ''; return; }
  let num = (parseInt(v, 10) / 100).toFixed(2);
  let parts = num.split('.');
  let intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  input.value = 'R$ ' + intPart + ',' + parts[1];
}

function attachFormatters() {
  document.querySelectorAll('input[id$="_cep"]').forEach(el => {
    el.addEventListener('input', () => formatCEP(el));
  });
  document.querySelectorAll('input[id$="_cpf"]').forEach(el => {
    el.addEventListener('input', () => formatCPF(el));
  });
  document.querySelectorAll('input[id$="_nasc"]').forEach(el => {
    el.addEventListener('input', () => formatDate(el));
  });
  document.querySelectorAll('input[id$="_data_envio"], input[id$="_data_evento"]').forEach(el => {
    el.addEventListener('input', () => formatDate(el));
  });
  document.querySelectorAll('input[id$="_valor_solicitado"], input[id$="_valor_aprovado"]').forEach(el => {
    el.addEventListener('blur', () => formatCurrency(el));
  });
}

function collectData(prefix) {
  const getVal = (id) => {
    const el = document.getElementById(prefix + '_' + id);
    return el ? el.value : '';
  };
  return {
    nusp: getVal('nusp'),
    nome: getVal('nome'),
    dpto: getVal('dpto'),
    email: getVal('email'),
    vinculo: getVal('vinculo'),
    matricula: getVal('matricula'),
    ano_ingresso: getVal('ano'),
    orientador: getVal('orientador'),
    curso: getVal('curso'),
    status: getVal('status'),
    email_pessoal: getVal('email2'),
    telefone_celular: getVal('tel'),
    cep: getVal('cep'),
    data_nascimento: getVal('nasc'),
    uf: getVal('uf'),
    complemento: getVal('complemento'),
    sexo: getVal('sexo'),
    cpf: getVal('cpf'),
    logradouro: getVal('rua'),
    numero: getVal('num'),
    bairro: getVal('bairro'),
    cidade: getVal('cidade'),
    valor_solicitado: getVal('valor_solicitado'),
    valor_aprovado: getVal('valor_aprovado'),
    assunto: getVal('assunto'),
    curso_aux: getVal('curso_aux'),
    data_evento: getVal('data_evento'),
    local: getVal('local'),
    agencia: getVal('agencia'),
    conta: getVal('conta'),
    data_envio: getVal('data_envio'),
    tipo: prefix
  };
}

async function submitForm(prefix) {
  const errorEl = document.getElementById('error-' + prefix);
  errorEl.textContent = '';
  
  const data = collectData(prefix);
  
  try {
    const response = await fetch(API_BASE + '/api/solicitar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (!result.ok) {
      errorEl.textContent = result.errors.join('\n');
      return;
    }
    
    showResult(prefix, result);
    
  } catch (e) {
    errorEl.textContent = 'Erro de conexão. Verifique se o servidor está ativo.';
  }
}

function showResult(prefix, result) {
  const formSection = document.getElementById('form-section');
  const resultDiv = document.getElementById('result');
  
  let html = '<h2>Solicitação registrada</h2>';
  
  html += '<div class="info-grid">';
  for (const [key, value] of Object.entries(result.data)) {
    if (value) {
      html += '<div><strong>' + key + ':</strong> ' + value + '</div>';
    }
  }
  html += '</div>';
  
  html += '<h3>Ofício de resposta</h3>';
  html += '<div class="oficio">' + result.oficio + '</div>';
  
  resultDiv.innerHTML = html;
  resultDiv.style.display = 'block';
  formSection.style.display = 'none';
  window.scrollTo(0, 0);
}

document.addEventListener('DOMContentLoaded', attachFormatters);
