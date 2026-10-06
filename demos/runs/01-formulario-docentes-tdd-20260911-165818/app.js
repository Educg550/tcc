function apenasDigitos(valor) {
  return valor.replace(/\D/g, '');
}

function formatarMoeda(valor) {
  const digitos = apenasDigitos(valor);
  if (!digitos) {
    return '';
  }
  const centavos = parseInt(digitos, 10);
  const reais = Math.floor(centavos / 100);
  const resto = centavos % 100;
  return `R$ ${reais.toLocaleString('pt-BR')},${String(resto).padStart(2, '0')}`;
}

function formatarCpf(valor) {
  const d = apenasDigitos(valor).slice(0, 11);
  if (d.length < 11) {
    return valor;
  }
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9, 11)}`;
}

function formatarCep(valor) {
  const d = apenasDigitos(valor).slice(0, 8);
  if (d.length < 8) {
    return valor;
  }
  return `${d.slice(0, 5)}-${d.slice(5, 8)}`;
}

function formatarData(valor) {
  const d = apenasDigitos(valor).slice(0, 8);
  if (d.length < 8) {
    return valor;
  }
  return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4, 8)}`;
}

const MASCARAS = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData,
};

function coletarDados(form, aba) {
  const dados = { aba };
  form.querySelectorAll('[data-campo]').forEach((campo) => {
    const nome = campo.dataset.campo;
    if (nome === 'VALOR SOLICITADO (R$)') {
      const digitos = apenasDigitos(campo.value);
      dados[nome] = digitos ? parseInt(digitos, 10) / 100 : 0;
    } else {
      dados[nome] = campo.value;
    }
  });
  return dados;
}

async function enviarFormulario(form, aba) {
  const dados = coletarDados(form, aba);
  const resposta = await fetch('/api/solicitacao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
  });
  const corpo = await resposta.json();
  const divErros = document.getElementById(`erros-${aba}`);

  if (corpo.erros) {
    divErros.textContent = corpo.erros.join('\n');
    return;
  }

  divErros.textContent = '';
  document.getElementById('area-formularios').classList.add('oculto');
  document.getElementById('confirmacao').classList.remove('oculto');
  document.getElementById('oficio-texto').textContent = corpo.oficio;
}

function iniciar() {
  document.querySelectorAll('[data-mascara]').forEach((campo) => {
    campo.addEventListener('blur', () => {
      const tipo = campo.dataset.mascara;
      campo.value = MASCARAS[tipo](campo.value);
    });
  });

  document.querySelectorAll('.aba-botao').forEach((botao) => {
    botao.addEventListener('click', () => {
      document.querySelectorAll('.aba-botao').forEach((b) => b.classList.remove('ativo'));
      document.querySelectorAll('.formulario').forEach((f) => f.classList.remove('ativo'));
      botao.classList.add('ativo');
      document.getElementById(`form-${botao.dataset.aba}`).classList.add('ativo');
    });
  });

  document.getElementById('form-alunos').addEventListener('submit', (evento) => {
    evento.preventDefault();
    enviarFormulario(evento.target, 'alunos');
  });

  document.getElementById('form-docentes').addEventListener('submit', (evento) => {
    evento.preventDefault();
    enviarFormulario(evento.target, 'docentes');
  });
}

document.addEventListener('DOMContentLoaded', iniciar);
