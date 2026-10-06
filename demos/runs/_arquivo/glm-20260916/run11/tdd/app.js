function soDigitos(texto) {
  return texto.replace(/\D/g, '');
}

function formatarMoeda(texto) {
  const d = soDigitos(texto);
  if (!d) return '';
  const centavos = d.slice(-2).padStart(2, '0');
  const inteiro = (d.slice(0, -2) || '0').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + inteiro + ',' + centavos;
}

function formatarCPF(texto) {
  const d = soDigitos(texto).slice(0, 11);
  let saida = d.slice(0, 3);
  if (d.length > 3) saida += '.' + d.slice(3, 6);
  if (d.length > 6) saida += '.' + d.slice(6, 9);
  if (d.length > 9) saida += '-' + d.slice(9, 11);
  return saida;
}

function formatarCEP(texto) {
  const d = soDigitos(texto).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
}

function formatarData(texto) {
  const d = soDigitos(texto).slice(0, 8);
  let saida = d.slice(0, 2);
  if (d.length > 2) saida += '/' + d.slice(2, 4);
  if (d.length > 4) saida += '/' + d.slice(4, 8);
  return saida;
}

const FORMATOS = {
  moeda: formatarMoeda,
  cpf: formatarCPF,
  cep: formatarCEP,
  data: formatarData,
};

document.querySelectorAll('[data-formato]').forEach((campo) => {
  campo.addEventListener('blur', () => {
    campo.value = FORMATOS[campo.dataset.formato](campo.value);
  });
});

const abas = document.querySelectorAll('.aba');
const formularios = document.querySelectorAll('.formulario');

abas.forEach((aba) => {
  aba.addEventListener('click', () => {
    abas.forEach((outra) => outra.classList.toggle('ativa', outra === aba));
    formularios.forEach((form) => {
      form.hidden = form.dataset.aba !== aba.dataset.aba;
    });
  });
});

formularios.forEach((form) => {
  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const caixa = form.querySelector('.erros');
    caixa.hidden = true;
    const corpo = { aba: form.dataset.aba };
    form.querySelectorAll('[data-rotulo]').forEach((campo) => {
      corpo[campo.dataset.rotulo] = campo.value.trim();
    });
    const resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(corpo),
    });
    const dados = await resposta.();
    if (!dados.ok) {
      caixa.textContent = dados.erros.join('\n');
      caixa.hidden = false;
      return;
    }
    document.querySelector('.abas').hidden = true;
    formularios.forEach((outro) => {
      outro.hidden = true;
    });
    document.getElementById('oficio').textContent = dados.oficio;
    document.getElementById('confirmacao').hidden = false;
  });
});
