const abas = document.querySelectorAll('.aba');
const paineis = {
  alunos: document.getElementById('form-alunos'),
  docentes: document.getElementById('form-docentes')
};

abas.forEach(function (botao) {
  botao.addEventListener('click', function () {
    abas.forEach(function (outro) {
      const ativo = outro === botao;
      outro.classList.toggle('ativa', ativo);
      outro.setAttribute('aria-selected', ativo ? 'true' : 'false');
    });
    Object.keys(paineis).forEach(function (nome) {
      paineis[nome].hidden = nome !== botao.dataset.aba;
    });
  });
});

function apenasDigitos(valor) {
  return valor.replace(/\D/g, '');
}

function formatarMoeda(digitos) {
  const centavos = parseInt(digitos, 10);
  const inteiro = Math.floor(centavos / 100).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + inteiro + ',' + String(centavos % 100).padStart(2, '0');
}

function formatarCPF(digitos) {
  const d = digitos.slice(0, 11);
  let saida = d.slice(0, 3);
  if (d.length > 3) saida += '.' + d.slice(3, 6);
  if (d.length > 6) saida += '.' + d.slice(6, 9);
  if (d.length > 9) saida += '-' + d.slice(9, 11);
  return saida;
}

function formatarCEP(digitos) {
  const d = digitos.slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(digitos) {
  const d = digitos.slice(0, 8);
  let saida = d.slice(0, 2);
  if (d.length > 2) saida += '/' + d.slice(2, 4);
  if (d.length > 4) saida += '/' + d.slice(4, 8);
  return saida;
}

const mascaras = {
  valor: formatarMoeda,
  cpf: formatarCPF,
  cep: formatarCEP,
  data_nascimento: formatarData
};

function aplicarMascara(input) {
  const formatar = mascaras[input.name];
  if (!formatar) return;
  const digitos = apenasDigitos(input.value);
  input.value = digitos ? formatar(digitos) : '';
}

document.querySelectorAll('input[name]').forEach(function (input) {
  if (mascaras[input.name]) {
    input.addEventListener('blur', function () { aplicarMascara(input); });
  }
});

function mostrarErros(form, mensagens) {
  const caixa = form.querySelector('.erros');
  caixa.replaceChildren.apply(caixa, mensagens.map(function (mensagem) {
    const linha = document.createElement('p');
    linha.textContent = mensagem;
    return linha;
  }));
  caixa.hidden = false;
}

Object.keys(paineis).forEach(function (nome) {
  const form = paineis[nome];
  form.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    form.querySelectorAll('input[name]').forEach(aplicarMascara);
    const dados = Object.fromEntries(new FormData(form));
    dados.aba = nome;

    const resposta = await fetch('/api/solicitar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados)
    });
    const resultado = await resposta.json();

    if (resultado.erros) {
      mostrarErros(form, resultado.erros);
      return;
    }

    form.querySelector('.erros').hidden = true;
    document.getElementById('formulario').hidden = true;
    document.getElementById('oficio').textContent = resultado.oficio;
    document.getElementById('confirmacao').hidden = false;
  });
});
