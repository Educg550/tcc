// Alternância de abas
const abaAlunos = document.getElementById('aba-alunos');
const abaDocentes = document.getElementById('aba-docentes');
const formAlunos = document.getElementById('form-alunos');
const formDocentes = document.getElementById('form-docentes');

function mostrarAba(aba) {
  const alunos = aba === 'alunos';
  abaAlunos.classList.toggle('ativa', alunos);
  abaDocentes.classList.toggle('ativa', !alunos);
  formAlunos.classList.toggle('ativo', alunos);
  formDocentes.classList.toggle('ativo', !alunos);
}

abaAlunos.addEventListener('click', () => mostrarAba('alunos'));
abaDocentes.addEventListener('click', () => mostrarAba('docentes'));

// Formatação de campos
function apenasDigitos(texto) {
  return texto.replace(/\D/g, '');
}

function formatarValor(digitos) {
  if (!digitos) return '';
  const centavos = parseInt(digitos, 10);
  const reais = Math.floor(centavos / 100);
  const resto = (centavos % 100).toString().padStart(2, '0');
  const reaisStr = reais.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `R$ ${reaisStr},${resto}`;
}

function formatarCpf(digitos) {
  return digitos
    .slice(0, 11)
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/(\d{3})\.(\d{3})\.(\d{3})(\d)/, '$1.$2.$3-$4');
}

function formatarCep(digitos) {
  return digitos.slice(0, 8).replace(/(\d{5})(\d)/, '$1-$2');
}

function formatarData(digitos) {
  return digitos
    .slice(0, 8)
    .replace(/(\d{2})(\d)/, '$1/$2')
    .replace(/(\d{2})\/(\d{2})(\d)/, '$1/$2/$3');
}

const formatadores = {
  valor_solicitado: (d) => formatarValor(d),
  cpf: (d) => formatarCpf(d),
  cep: (d) => formatarCep(d),
  data_nascimento: (d) => formatarData(d),
};

[formAlunos, formDocentes].forEach((form) => {
  form.querySelectorAll('input[name]').forEach((campo) => {
    const formatador = formatadores[campo.name];
    if (!formatador) return;
    campo.addEventListener('blur', () => {
      campo.value = formatador(apenasDigitos(campo.value));
    });
  });
});

// Envio das solicitações
const areaFormulario = document.getElementById('area-formulario');
const areaConfirmacao = document.getElementById('area-confirmacao');
const divOficio = document.getElementById('oficio');

async function enviar(form, aba, divErros) {
  divErros.innerHTML = '';
  divErros.style.display = 'none';

  const dados = Object.fromEntries(new FormData(form).entries());
  dados.aba = aba;

  try {
    const resposta = await fetch('/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();
    if (!resultado.ok) {
      resultado.erros.forEach((msg) => {
        const p = document.createElement('p');
        p.textContent = msg;
        divErros.appendChild(p);
      });
      divErros.style.display = 'block';
      divErros.scrollIntoView({ block: 'nearest' });
      return;
    }
    divOficio.textContent = resultado.oficio;
    areaFormulario.classList.add('oculto');
    areaConfirmacao.classList.remove('oculto');
  } catch (erro) {
    const p = document.createElement('p');
    p.textContent = 'Não foi possível enviar a solicitação.';
    divErros.appendChild(p);
    divErros.style.display = 'block';
  }
}

formAlunos.addEventListener('submit', (e) => {
  e.preventDefault();
  enviar(formAlunos, 'alunos', document.getElementById('erros-alunos'));
});

formDocentes.addEventListener('submit', (e) => {
  e.preventDefault();
  enviar(formDocentes, 'docentes', document.getElementById('erros-docentes'));
});
