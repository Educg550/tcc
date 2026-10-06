const formatadores = {
  valor: valor => {
    const digitos = valor.replace(/\D/g, '').replace(/^0+/, '');
    if (!digitos) return '';
    const numero = digitos.padStart(3, '0');
    const inteiro = numero.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return `R$ ${inteiro},${numero.slice(-2)}`;
  },
  cpf: valor => {
    const d = valor.replace(/\D/g, '').slice(0, 11);
    if (d.length > 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
    if (d.length > 6) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
    if (d.length > 3) return `${d.slice(0, 3)}.${d.slice(3)}`;
    return d;
  },
  cep: valor => {
    const d = valor.replace(/\D/g, '').slice(0, 8);
    return d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
  },
  nascimento: valor => {
    const d = valor.replace(/\D/g, '').slice(0, 8);
    return [d.slice(0, 2), d.slice(2, 4), d.slice(4, 8)].filter(Boolean).join('/');
  }
};

const formularios = document.querySelectorAll('.formulario');
const abas = document.querySelectorAll('.aba');
const confirmacao = document.getElementById('confirmacao');

formularios.forEach(formulario => {
  formulario.querySelectorAll('input, select, textarea').forEach(campo => {
    const formatador = formatadores[campo.name];
    if (formatador) {
      campo.addEventListener('blur', () => { campo.value = formatador(campo.value); });
    }
  });

  formulario.addEventListener('submit', async evento => {
    evento.preventDefault();

    formulario.querySelectorAll('input, select, textarea').forEach(campo => {
      const formatador = formatadores[campo.name];
      if (formatador) campo.value = formatador(campo.value);
    });

    const dados = new FormData(formulario);
    dados.set('tipo', formulario.dataset.painel === 'docentes' ? 'docente' : 'aluno');

    const resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(Object.fromEntries(dados))
    });
    const resultado = await resposta.json();

    const caixaErros = formulario.querySelector('.erros');
    if (!resultado.valido) {
      caixaErros.textContent = resultado.erros.join('\n');
      return;
    }

    caixaErros.textContent = '';
    document.getElementById('oficio').textContent = resultado.oficio;
    formularios.forEach(outro => outro.classList.add('oculto'));
    confirmacao.classList.remove('oculto');
  });
});

abas.forEach(aba => {
  aba.addEventListener('click', () => {
    abas.forEach(outra => {
      const ativa = outra === aba;
      outra.classList.toggle('ativa', ativa);
      outra.setAttribute('aria-selected', String(ativa));
    });
    confirmacao.classList.add('oculto');
    formularios.forEach(formulario => {
      formulario.classList.toggle('oculto', formulario.dataset.painel !== aba.dataset.aba);
    });
  });
});
