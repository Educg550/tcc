const FORMATO = {
  moeda(v) {
    const d = v.replace(/\D/g, '');
    if (!d) return '';
    const centavos = d.slice(-2).padStart(2, '0');
    const reais = d.slice(0, -2).replace(/^0+(?=\d)/, '');
    return 'R$ ' + (reais.replace(/\B(?=(\d{3})+(?!\d))/g, '.') || '0') + ',' + centavos;
  },
  cpf(v) {
    const d = v.replace(/\D/g, '').slice(0, 11);
    let r = d.slice(0, 3);
    if (d.length > 3) r += '.' + d.slice(3, 6);
    if (d.length > 6) r += '.' + d.slice(6, 9);
    if (d.length > 9) r += '-' + d.slice(9);
    return r;
  },
  cep(v) {
    const d = v.replace(/\D/g, '').slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  },
  data(v) {
    const d = v.replace(/\D/g, '').slice(0, 8);
    let r = d.slice(0, 2);
    if (d.length > 2) r += '/' + d.slice(2, 4);
    if (d.length > 4) r += '/' + d.slice(4);
    return r;
  },
};

document.querySelectorAll('[data-formato]').forEach((campo) => {
  campo.addEventListener('blur', () => {
    campo.value = FORMATO[campo.dataset.formato](campo.value);
  });
});

function mostrarAba(aba) {
  document.querySelectorAll('.aba').forEach((botao) => botao.classList.toggle('ativa', botao.dataset.aba === aba));
  document.getElementById('form-alunos').hidden = aba !== 'alunos';
  document.getElementById('form-docentes').hidden = aba !== 'docentes';
}

document.querySelectorAll('.aba').forEach((botao) => {
  botao.addEventListener('click', () => mostrarAba(botao.dataset.aba));
});

document.querySelectorAll('form').forEach((form) => {
  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const aba = form.id.replace('form-', '');
    const caixa = document.getElementById('erros-' + aba);
    caixa.hidden = true;
    caixa.replaceChildren();
    const campos = {};
    form.querySelectorAll('[data-campo]').forEach((campo) => {
      campos[campo.dataset.campo] = campo.value;
    });
    const resposta = await fetch('/solicitar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify({ aba: aba, campos: campos }),
    });
    const corpo = await resposta.();
    if (corpo.oficio !== undefined) {
      document.getElementById('oficio').textContent = corpo.oficio;
      document.getElementById('pagina-formulario').hidden = true;
      document.getElementById('confirmacao').hidden = false;
    } else {
      corpo.erros.forEach((mensagem) => {
        const linha = document.createElement('p');
        linha.textContent = mensagem;
        caixa.appendChild(linha);
      });
      caixa.hidden = false;
    }
  });
});
