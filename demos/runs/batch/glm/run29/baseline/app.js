// Comportamento de tela: abas, formatação automática e envio ao backend.

const PAINELS = {
  alunos: document.getElementById('form-alunos'),
  docentes: document.getElementById('form-docentes'),
};
const ERROS = {
  alunos: document.getElementById('erros-alunos'),
  docentes: document.getElementById('erros-docentes'),
};
const CONFIRMACAO = document.getElementById('confirmacao');
const OFICIO = document.getElementById('oficio');
let abaAtiva = 'alunos';

// Formatação automática de moeda, CPF, CEP e data.
function soDigitos(texto) {
  return (texto.match(/\d/g) || []).join('');
}

function formatarMoeda(texto) {
  const digitos = soDigitos(texto);
  if (!digitos) return '';
  const centavos = parseInt(digitos, 10);
  const reais = Math.floor(centavos / 100);
  const resto = (centavos % 100).toString().padStart(2, '0');
  const partes = reais.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + partes + ',' + resto;
}

function formatarCpf(texto) {
  const digitos = soDigitos(texto).slice(0, 11).padStart(0, '');
  return digitos.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

function formatarCep(texto) {
  return soDigitos(texto).slice(0, 8).replace(/^(\d{5})(\d{3})$/, '$1-$2');
}

function formatarData(texto) {
  return soDigitos(texto).slice(0, 8).replace(/^(\d{2})(\d{2})(\d{4})$/, '$1/$2/$3');
}

for (const form of document.querySelectorAll('form')) {
  form.addEventListener('focusout', (e) => {
    const campo = e.target;
    if (campo.name === 'valor') {
      campo.value = formatarMoeda(campo.value);
    } else if (campo.name === 'cpf') {
      campo.value = formatarCpf(campo.value);
    } else if (campo.name === 'cep') {
      campo.value = formatarCep(campo.value);
    } else if (campo.name === 'data_nascimento') {
      campo.value = formatarData(campo.value);
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const aba = form.dataset.aba;
    const dados = { aluno: aba === 'alunos' };
    for (const campo of form.elements) {
      if (campo.name) dados[campo.name] = campo.value;
    }
    const resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();
    if (resultado.erros) {
      const lista = ERROS[aba];
      lista.innerHTML = '';
      for (const erro of resultado.erros) {
        const li = document.createElement('li');
        li.textContent = erro;
        lista.appendChild(li);
      }
      lista.hidden = false;
    } else {
      ERROS[aba].hidden = true;
      OFICIO.textContent = resultado.oficio;
      CONFIRMACAO.hidden = false;
      PAINELS.alunos.hidden = true;
      PAINELS.docentes.hidden = true;
    }
  });
}

// Abas: trocar sem recarregar nem perder o que foi digitado.
document.getElementById('tab-alunos').addEventListener('click', () => {
  abaAtiva = 'alunos';
  PAINELS.alunos.hidden = false;
  PAINELS.docentes.hidden = true;
  document.getElementById('tab-alunos').classList.add('ativa');
  document.getElementById('tab-docentes').classList.remove('ativa');
});

document.getElementById('tab-docentes').addEventListener('click', () => {
  abaAtiva = 'docentes';
  PAINELS.docentes.hidden = false;
  PAINELS.alunos.hidden = true;
  document.getElementById('tab-docentes').classList.add('ativa');
  document.getElementById('tab-alunos').classList.remove('ativa');
});
