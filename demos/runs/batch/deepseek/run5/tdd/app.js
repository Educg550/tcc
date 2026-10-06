const soDigitos = (texto) => texto.replace(/\D/g, '');

const milhar = (numero) => String(numero).replace(/\B(?=(\d{3})+(?!\d))/g, '.');

function formatarMoeda(input) {
  const digitos = soDigitos(input.value);
  if (!digitos) {
    input.value = '';
    return;
  }
  const total = parseInt(digitos, 10);
  const centavos = String(total % 100).padStart(2, '0');
  input.value = `R$ ${milhar(Math.floor(total / 100))},${centavos}`;
}

function formatarCPF(input) {
  const digitos = soDigitos(input.value).slice(0, 11);
  input.value = digitos
    .replace(/^(\d{3})(\d)/, '$1.$2')
    .replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/^(\d{3})\.(\d{3})\.(\d{3})(\d)/, '$1.$2.$3-$4');
}

function formatarCEP(input) {
  const digitos = soDigitos(input.value).slice(0, 8);
  input.value = digitos.replace(/^(\d{5})(\d)/, '$1-$2');
}

function formatarData(input) {
  const digitos = soDigitos(input.value).slice(0, 8);
  input.value = digitos
    .replace(/^(\d{2})(\d)/, '$1/$2')
    .replace(/^(\d{2})\/(\d{2})(\d)/, '$1/$2/$3');
}

const formatadores = {
  moeda: formatarMoeda,
  cpf: formatarCPF,
  cep: formatarCEP,
  data: formatarData,
};

document.querySelectorAll('[data-formato]').forEach((input) => {
  input.addEventListener('blur', () => formatadores[input.dataset.formato](input));
});

document.querySelectorAll('.aba').forEach((aba) => {
  aba.addEventListener('click', () => {
    document.querySelectorAll('.aba').forEach((outra) => {
      outra.classList.toggle('ativa', outra === aba);
    });
    document.querySelectorAll('.formulario').forEach((form) => {
      form.classList.toggle('ativo', form.id === `form-${aba.dataset.aba}`);
    });
  });
});

document.querySelectorAll('.formulario').forEach((form) => {
  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();

    const resposta = await fetch('/solicitar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(Object.fromEntries(new FormData(form))),
    });
    const resultado = await resposta.json();

    if (resultado.ok) {
      document.querySelector('.abas').hidden = true;
      document.querySelectorAll('.formulario').forEach((outro) => {
        outro.hidden = true;
      });
      const confirmacao = document.getElementById('confirmacao');
      confirmacao.querySelector('.oficio').textContent = resultado.oficio;
      confirmacao.hidden = false;
      return;
    }

    const caixa = form.querySelector('.erros');
    caixa.replaceChildren(
      ...resultado.erros.map((mensagem) => {
        const linha = document.createElement('p');
        linha.textContent = mensagem;
        return linha;
      })
    );
    caixa.hidden = false;
  });
});
