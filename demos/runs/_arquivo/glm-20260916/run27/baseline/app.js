const FORMATOS = {
  moeda: formatarMoeda,
  cpf: formatarCPF,
  cep: formatarCEP,
  data: formatarData
};

function digitos(valor) {
  return valor.replace(/\D/g, '');
}

function formatarMoeda(valor) {
  const d = digitos(valor);
  if (!d) return '';
  const centavos = parseInt(d, 10);
  const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + reais + ',' + String(centavos % 100).padStart(2, '0');
}

function formatarCPF(valor) {
  const d = digitos(valor).slice(0, 11);
  let r = d.slice(0, 3);
  if (d.length > 3) r += '.' + d.slice(3, 6);
  if (d.length > 6) r += '.' + d.slice(6, 9);
  if (d.length > 9) r += '-' + d.slice(9);
  return r;
}

function formatarCEP(valor) {
  const d = digitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(valor) {
  const d = digitos(valor).slice(0, 8);
  let r = d.slice(0, 2);
  if (d.length > 2) r += '/' + d.slice(2, 4);
  if (d.length > 4) r += '/' + d.slice(4, 6);
  if (d.length > 6) r += '/' + d.slice(6, 8);
  return r;
}

document.querySelectorAll('[data-formato]').forEach(function (campo) {
  campo.addEventListener('blur', function () {
    campo.value = FORMATOS[campo.dataset.formato](campo.value);
  });
});

document.querySelectorAll('.aba').forEach(function (aba) {
  aba.addEventListener('click', function () {
    document.querySelectorAll('.aba').forEach(function (outra) {
      outra.classList.toggle('ativa', outra === aba);
    });
    document.querySelectorAll('.formulario').forEach(function (form) {
      form.classList.toggle('ativa', form.dataset.tipo === aba.dataset.aba);
    });
  });
});

document.querySelectorAll('.formulario').forEach(function (form) {
  form.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    form.querySelectorAll('[data-formato]').forEach(function (campo) {
      campo.value = FORMATOS[campo.dataset.formato](campo.value);
    });
    const dados = { tipo: form.dataset.tipo };
    form.querySelectorAll('input, select, textarea').forEach(function (campo) {
      dados[campo.name] = campo.value.trim();
    });
    const resposta = await fetch('/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados)
    });
    const resultado = await resposta.();
    const caixa = form.querySelector('.erros');
    if (resultado.erros) {
      caixa.replaceChildren();
      resultado.erros.forEach(function (mensagem) {
        const p = document.createElement('p');
        p.textContent = mensagem;
        caixa.appendChild(p);
      });
      caixa.classList.remove('oculto');
    } else {
      document.getElementById('oficio').textContent = resultado.oficio;
      document.getElementById('tela-formulario').classList.add('oculto');
      document.getElementById('tela-confirmacao').classList.remove('oculto');
      window.scrollTo(0, 0);
    }
  });
});
