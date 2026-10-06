'use strict';

const semDigitos = (valor) => valor.replace(/\D/g, '');

const FORMATADORES = {
  valor_solicitado(campo) {
    const digitos = semDigitos(campo.value);
    if (!digitos) {
      campo.value = '';
      return;
    }
    const centavos = BigInt(digitos);
    const reais = (centavos / 100n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    const resto = (centavos % 100n).toString().padStart(2, '0');
    campo.value = `R$ ${reais},${resto}`;
  },
  cpf(campo) {
    const d = semDigitos(campo.value).slice(0, 11);
    if (d.length > 9) {
      campo.value = `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
    } else if (d.length > 6) {
      campo.value = `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
    } else if (d.length > 3) {
      campo.value = `${d.slice(0, 3)}.${d.slice(3)}`;
    } else {
      campo.value = d;
    }
  },
  cep(campo) {
    const d = semDigitos(campo.value).slice(0, 8);
    campo.value = d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
  },
  data_nascimento(campo) {
    const d = semDigitos(campo.value).slice(0, 8);
    if (d.length > 4) {
      campo.value = `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
    } else if (d.length > 2) {
      campo.value = `${d.slice(0, 2)}/${d.slice(2)}`;
    } else {
      campo.value = d;
    }
  },
};

document.querySelectorAll('.aba').forEach((aba) => {
  aba.addEventListener('click', () => {
    document.querySelectorAll('.aba').forEach((outra) => outra.classList.toggle('ativa', outra === aba));
    document.querySelectorAll('.painel').forEach((painel) => {
      painel.hidden = painel.id !== aba.dataset.alvo;
    });
  });
});

document.querySelectorAll('form').forEach((form) => {
  Object.keys(FORMATADORES).forEach((nome) => {
    const campo = form.elements[nome];
    if (campo) {
      campo.addEventListener('blur', () => FORMATADORES[nome](campo));
    }
  });

  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const dados = { aba: form.dataset.aba };
    form.querySelectorAll('[name]').forEach((campo) => {
      dados[campo.name] = campo.name === 'valor_solicitado' ? semDigitos(campo.value) : campo.value;
    });
    const resposta = await fetch('/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados),
    });
    const corpo = await resposta.();
    const caixa = form.querySelector('.erros');
    if (corpo.erros) {
      caixa.replaceChildren(...corpo.erros.map((mensagem) => {
        const paragrafo = document.createElement('p');
        paragrafo.textContent = mensagem;
        return paragrafo;
      }));
      caixa.hidden = false;
      return;
    }
    document.getElementById('formulario').hidden = true;
    document.getElementById('texto-oficio').textContent = corpo.oficio;
    document.getElementById('confirmacao').hidden = false;
    window.scrollTo(0, 0);
  });
});
