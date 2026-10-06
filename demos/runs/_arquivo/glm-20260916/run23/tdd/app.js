function apenasDigitos(texto) {
  return texto.replace(/\D/g, '');
}

function formatarMoeda(texto) {
  const digitos = apenasDigitos(texto);
  if (!digitos) {
    return '';
  }
  const reais = digitos.slice(0, -2) || '0';
  const centavos = digitos.slice(-2).padStart(2, '0');
  const milhar = reais.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + milhar + ',' + centavos;
}

function formatarCpf(texto) {
  const d = apenasDigitos(texto).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return d.slice(0, 3) + '.' + d.slice(3);
  if (d.length <= 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
  return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
}

function formatarCep(texto) {
  const d = apenasDigitos(texto).slice(0, 8);
  if (d.length <= 5) return d;
  return d.slice(0, 5) + '-' + d.slice(5);
}

function formatarData(texto) {
  const d = apenasDigitos(texto).slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
  return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
}

const FORMATADORES = {
  valor: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData,
};

document.querySelectorAll('[data-formato]').forEach((campo) => {
  campo.addEventListener('blur', () => {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  });
});

document.querySelectorAll('.aba').forEach((botao) => {
  botao.addEventListener('click', () => {
    document.querySelectorAll('.aba').forEach((b) => b.classList.toggle('ativa', b === botao));
    document.querySelectorAll('.formulario').forEach((form) => {
      form.hidden = form.dataset.aba !== botao.dataset.aba;
    });
  });
});

document.querySelectorAll('.formulario').forEach((form) => {
  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const erros = form.querySelector('.erros');
    erros.textContent = '';
    const dados = {};
    new FormData(form).forEach((valor, chave) => {
      dados[chave] = valor;
    });
    dados.aba = form.dataset.aba;
    try {
      const resposta = await fetch('/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/' },
        body: JSON.stringify(dados),
      });
      const corpo = await resposta.();
      if (corpo.oficio) {
        document.querySelectorAll('.formulario, .abas').forEach((elemento) => {
          elemento.hidden = true;
        });
        document.getElementById('oficio').textContent = corpo.oficio;
        document.getElementById('confirmacao').hidden = false;
      } else {
        corpo.erros.forEach((mensagem) => {
          const linha = document.createElement('p');
          linha.textContent = mensagem;
          erros.appendChild(linha);
        });
      }
    } catch (erro) {
      const linha = document.createElement('p');
      linha.textContent = 'Não foi possível enviar a solicitação.';
      erros.appendChild(linha);
    }
  });
});
