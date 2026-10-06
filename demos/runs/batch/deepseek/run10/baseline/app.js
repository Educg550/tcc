const abas = document.querySelectorAll('.aba');
const forms = {
  alunos: document.getElementById('form-alunos'),
  docentes: document.getElementById('form-docentes'),
};

abas.forEach(function (aba) {
  aba.addEventListener('click', function () {
    const alvo = aba.dataset.aba;
    abas.forEach(function (outra) {
      outra.classList.toggle('ativa', outra === aba);
    });
    forms.alunos.classList.toggle('escondido', alvo !== 'alunos');
    forms.docentes.classList.toggle('escondido', alvo !== 'docentes');
  });
});

function formataMoeda(valor) {
  const digitos = valor.replace(/\D/g, '');
  if (!digitos) return '';
  const completo = digitos.padStart(3, '0');
  const centavos = completo.slice(-2);
  const reais = completo.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + reais + ',' + centavos;
}

function formataCpf(valor) {
  const d = valor.replace(/\D/g, '').slice(0, 11);
  let saida = d;
  if (d.length > 3) saida = d.slice(0, 3) + '.' + d.slice(3);
  if (d.length > 6) saida = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
  if (d.length > 9) saida = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  return saida;
}

function formataCep(valor) {
  const d = valor.replace(/\D/g, '').slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formataData(valor) {
  const d = valor.replace(/\D/g, '').slice(0, 8);
  let saida = d;
  if (d.length > 2) saida = d.slice(0, 2) + '/' + d.slice(2);
  if (d.length > 4) saida = d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  return saida;
}

const formatadores = {
  valor: formataMoeda,
  cpf: formataCpf,
  cep: formataCep,
  data_nascimento: formataData,
};

Object.keys(formatadores).forEach(function (nome) {
  const fn = formatadores[nome];
  document.querySelectorAll('input[name="' + nome + '"]').forEach(function (campo) {
    campo.addEventListener('blur', function () {
      campo.value = fn(campo.value);
    });
  });
});

Object.keys(forms).forEach(function (nome) {
  const form = forms[nome];
  form.addEventListener('submit', function (evento) {
    evento.preventDefault();
    const dados = Object.fromEntries(new FormData(form).entries());
    dados.aba = nome;

    fetch('/api/solicitar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    })
      .then(function (resposta) { return resposta.json(); })
      .then(function (resultado) {
        const areaErros = form.querySelector('.erros');
        if (resultado.ok) {
          areaErros.textContent = '';
          document.getElementById('tela-form').classList.add('escondido');
          document.getElementById('tela-confirmacao').classList.remove('escondido');
          document.getElementById('oficio').textContent = resultado.oficio;
        } else {
          areaErros.textContent = '';
          resultado.erros.forEach(function (mensagem) {
            const p = document.createElement('p');
            p.textContent = mensagem;
            areaErros.appendChild(p);
          });
        }
      });
  });
});
