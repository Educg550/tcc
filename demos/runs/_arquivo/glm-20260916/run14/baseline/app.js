function soDigitos(valor) {
  return valor.replace(/\D/g, '');
}

function mascaraMoeda(valor) {
  const digitos = soDigitos(valor);
  if (!digitos) {
    return '';
  }
  const centavos = Number(digitos);
  const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  const centavosTexto = String(centavos % 100).padStart(2, '0');
  return 'R$ ' + reais + ',' + centavosTexto;
}

function mascaraCpf(valor) {
  const d = soDigitos(valor).slice(0, 11);
  let texto = d.slice(0, 3);
  if (d.length > 3) {
    texto += '.' + d.slice(3, 6);
  }
  if (d.length > 6) {
    texto += '.' + d.slice(6, 9);
  }
  if (d.length > 9) {
    texto += '-' + d.slice(9, 11);
  }
  return texto;
}

function mascaraCep(valor) {
  const d = soDigitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function mascaraData(valor) {
  const d = soDigitos(valor).slice(0, 8);
  let texto = d.slice(0, 2);
  if (d.length > 2) {
    texto += '/' + d.slice(2, 4);
  }
  if (d.length > 4) {
    texto += '/' + d.slice(4, 8);
  }
  return texto;
}

const MASCARAS = { moeda: mascaraMoeda, cpf: mascaraCpf, cep: mascaraCep, data: mascaraData };

function aplicarMascara(campo) {
  const mascara = MASCARAS[campo.dataset.mascara];
  if (mascara) {
    campo.value = mascara(campo.value);
  }
}

document.querySelectorAll('[data-mascara]').forEach(function (campo) {
  campo.addEventListener('blur', function () {
    aplicarMascara(campo);
  });
});

document.querySelectorAll('.aba').forEach(function (aba) {
  aba.addEventListener('click', function () {
    document.querySelectorAll('.aba').forEach(function (outra) {
      const ativa = outra === aba;
      outra.classList.toggle('ativa', ativa);
      outra.setAttribute('aria-selected', ativa ? 'true' : 'false');
      document.getElementById(outra.dataset.alvo).hidden = !ativa;
    });
  });
});

async function enviarFormulario(formulario) {
  formulario.querySelectorAll('[data-mascara]').forEach(aplicarMascara);
  const corpo = { perfil: formulario.dataset.perfil };
  new FormData(formulario).forEach(function (valor, nome) {
    corpo[nome] = valor;
  });
  const resposta = await fetch('/api/solicitacao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/' },
    body: JSON.stringify(corpo),
  });
  const dados = await resposta.();
  if (dados.ok) {
    document.getElementById('oficio').textContent = dados.oficio;
    document.getElementById('formularios').hidden = true;
    document.getElementById('confirmacao').hidden = false;
    window.scrollTo(0, 0);
    return;
  }
  const caixa = formulario.querySelector('.erros');
  caixa.replaceChildren(...dados.erros.map(function (mensagem) {
    const paragrafo = document.createElement('p');
    paragrafo.textContent = mensagem;
    return paragrafo;
  }));
  caixa.hidden = false;
  caixa.scrollIntoView({ block: 'nearest' });
}

document.querySelectorAll('form.solicitacao').forEach(function (formulario) {
  formulario.addEventListener('submit', function (evento) {
    evento.preventDefault();
    enviarFormulario(formulario);
  });
});
