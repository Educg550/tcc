const MASCARAS = {
  valor(valor) {
    const digitos = valor.replace(/\D/g, '').slice(0, 15);
    if (!digitos) return '';
    const centavos = parseInt(digitos, 10);
    return 'R$ ' + Math.floor(centavos / 100).toLocaleString('pt-BR') + ',' + String(centavos % 100).padStart(2, '0');
  },

  cpf(valor) {
    const digitos = valor.replace(/\D/g, '').slice(0, 11);
    let resultado = digitos.slice(0, 3);
    if (digitos.length > 3) resultado += '.' + digitos.slice(3, 6);
    if (digitos.length > 6) resultado += '.' + digitos.slice(6, 9);
    if (digitos.length > 9) resultado += '-' + digitos.slice(9, 11);
    return resultado;
  },

  cep(valor) {
    const digitos = valor.replace(/\D/g, '').slice(0, 8);
    return digitos.length > 5 ? digitos.slice(0, 5) + '-' + digitos.slice(5) : digitos;
  },

  data(valor) {
    const digitos = valor.replace(/\D/g, '').slice(0, 8);
    let resultado = digitos.slice(0, 2);
    if (digitos.length > 2) resultado += '/' + digitos.slice(2, 4);
    if (digitos.length > 4) resultado += '/' + digitos.slice(4, 8);
    return resultado;
  },
};

document.querySelectorAll('.aba').forEach(botao => {
  botao.addEventListener('click', () => {
    const aba = botao.dataset.aba;
    document.querySelectorAll('.aba').forEach(b => b.classList.toggle('ativa', b === botao));
    document.querySelectorAll('.painel').forEach(p => p.classList.toggle('ativo', p.id === 'painel-' + aba));
  });
});

document.querySelectorAll('.formulario').forEach(form => {
  const erros = form.querySelector('.erros');

  form.querySelectorAll('[data-mascara]').forEach(campo => {
    campo.addEventListener('blur', () => {
      campo.value = MASCARAS[campo.dataset.mascara](campo.value);
    });
  });

  form.addEventListener('submit', async evento => {
    evento.preventDefault();

    const dados = { aba: form.dataset.aba };
    form.querySelectorAll('[name]').forEach(campo => {
      dados[campo.name] = campo.value;
    });

    const resposta = await (await fetch('/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    })).json();

    if (resposta.ok) {
      mostrarConfirmacao(resposta.oficio);
      return;
    }

    erros.replaceChildren();
    resposta.erros.forEach(mensagem => {
      const linha = document.createElement('p');
      linha.textContent = mensagem;
      erros.appendChild(linha);
    });
  });
});

function mostrarConfirmacao(oficio) {
  document.getElementById('formularios').hidden = true;
  const confirmacao = document.getElementById('confirmacao');
  confirmacao.hidden = false;

  const titulo = document.createElement('h2');
  titulo.textContent = 'Solicitação registrada';

  const texto = document.createElement('pre');
  texto.textContent = oficio;

  confirmacao.replaceChildren(titulo, texto);
}
