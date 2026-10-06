const FORMATADORES = {
  valor: valor => {
    const d = valor.replace(/\D/g, '');
    if (!d) return '';
    const centavos = parseInt(d, 10);
    const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return 'R$ ' + reais + ',' + String(centavos % 100).padStart(2, '0');
  },
  cpf: valor => {
    const d = valor.replace(/\D/g, '').slice(0, 11);
    let formatado = d.slice(0, 3);
    if (d.length > 3) formatado += '.' + d.slice(3, 6);
    if (d.length > 6) formatado += '.' + d.slice(6, 9);
    if (d.length > 9) formatado += '-' + d.slice(9);
    return formatado;
  },
  cep: valor => {
    const d = valor.replace(/\D/g, '').slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  },
  data: valor => {
    const d = valor.replace(/\D/g, '').slice(0, 8);
    let formatado = d.slice(0, 2);
    if (d.length > 2) formatado += '/' + d.slice(2, 4);
    if (d.length > 4) formatado += '/' + d.slice(4);
    return formatado;
  }
};

document.querySelectorAll('[data-formato]').forEach(campo => {
  campo.addEventListener('blur', () => {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  });
});

const abas = document.querySelectorAll('.aba');
abas.forEach(aba => {
  aba.addEventListener('click', () => {
    abas.forEach(outra => {
      const ativa = outra === aba;
      outra.classList.toggle('ativa', ativa);
      outra.setAttribute('aria-selected', ativa ? 'true' : 'false');
    });
    document.querySelectorAll('.painel').forEach(painel => {
      painel.hidden = painel.id !== aba.dataset.painel;
    });
  });
});

document.querySelectorAll('form.solicitacao').forEach(form => {
  form.addEventListener('submit', evento => {
    evento.preventDefault();
    const caixa = form.querySelector('.erros');
    caixa.hidden = true;
    caixa.replaceChildren();
    const dados = Object.fromEntries(new FormData(form).entries());
    dados.tipo = form.dataset.tipo;
    fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados)
    })
      .then(resposta => resposta.())
      .then(resultado => {
        if (resultado.oficio) {
          document.getElementById('formulario-area').hidden = true;
          document.getElementById('oficio-texto').textContent = resultado.oficio;
          document.getElementById('confirmacao').hidden = false;
          window.scrollTo(0, 0);
        } else {
          resultado.erros.forEach(mensagem => {
            const paragrafo = document.createElement('p');
            paragrafo.textContent = mensagem;
            caixa.append(paragrafo);
          });
          caixa.hidden = false;
        }
      });
  });
});
