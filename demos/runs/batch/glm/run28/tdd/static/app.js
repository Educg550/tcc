const forms = {
  alunos: document.querySelector('#form-alunos'),
  docentes: document.querySelector('#form-docentes'),
};

function formatarMoeda(valor) {
  const digitos = valor.replace(/\D/g, '');
  if (!digitos) return '';
  const centavos = parseInt(digitos, 10);
  const reais = Math.floor(centavos / 100);
  const resto = (centavos % 100).toString().padStart(2, '0');
  return `R$ ${reais.toLocaleString('pt-BR')},${resto}`;
}

function formatarCPF(valor) {
  const d = valor.replace(/\D/g, '').slice(0, 11);
  let saida = d.slice(0, 3);
  if (d.length > 3) saida += '.' + d.slice(3, 6);
  if (d.length > 6) saida += '.' + d.slice(6, 9);
  if (d.length > 9) saida += '-' + d.slice(9);
  return saida;
}

function formatarCEP(valor) {
  const d = valor.replace(/\D/g, '').slice(0, 8);
  if (d.length > 5) return d.slice(0, 5) + '-' + d.slice(5);
  return d;
}

function formatarData(valor) {
  const d = valor.replace(/\D/g, '').slice(0, 8);
  let saida = d.slice(0, 2);
  if (d.length > 2) saida += '/' + d.slice(2, 4);
  if (d.length > 4) saida += '/' + d.slice(4);
  return saida;
}

function aoSairDoCampo(evento) {
  const campo = evento.target;
  if (campo.name === 'valor') campo.value = formatarMoeda(campo.value);
  if (campo.name === 'cpf') campo.value = formatarCPF(campo.value);
  if (campo.name === 'cep') campo.value = formatarCEP(campo.value);
  if (campo.name === 'data_nascimento') campo.value = formatarData(campo.value);
}

function coletarDados(form) {
  const dados = {};
  new FormData(form).forEach((valor, chave) => {
    dados[chave] = valor;
  });
  dados.valor = dados.valor.replace(/\D/g, '');
  dados.tipo = form.dataset.tipo;
  return dados;
}

function alternarAba(alvo) {
  Object.entries(forms).forEach(([nome, form]) => {
    form.hidden = nome !== alvo;
  });
  document.querySelectorAll('.aba').forEach((botao) => {
    botao.classList.toggle('ativa', botao.dataset.aba === alvo);
  });
}

document.querySelectorAll('.aba').forEach((botao) => {
  botao.addEventListener('click', () => alternarAba(botao.dataset.aba));
});

Object.values(forms).forEach((form) => {
  form.addEventListener('focusout', aoSairDoCampo);
  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const divErros = form.querySelector('.erros');
    divErros.hidden = true;
    divErros.innerHTML = '';
    const resposta = await fetch('/api/validar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(coletarDados(form)),
    });
    const resultado = await resposta.json();
    if (resultado.ok) {
      document.getElementById('formulario').hidden = true;
      const confirmacao = document.getElementById('confirmacao');
      document.getElementById('oficio').textContent = resultado.oficio;
      confirmacao.hidden = false;
    } else {
      resultado.erros.forEach((msg) => {
        const li = document.createElement('p');
        li.textContent = msg;
        divErros.appendChild(li);
      });
      divErros.hidden = false;
    }
  });
});
