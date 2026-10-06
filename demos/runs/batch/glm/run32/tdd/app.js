document.addEventListener('DOMContentLoaded', function () {
  const abas = document.querySelectorAll('.aba');
  const paineis = {
    alunos: document.getElementById('aba-alunos'),
    docentes: document.getElementById('aba-docentes'),
  };

  abas.forEach(function (aba) {
    aba.addEventListener('click', function () {
      abas.forEach(function (a) { a.classList.remove('ativa'); });
      aba.classList.add('ativa');
      Object.keys(paineis).forEach(function (nome) {
        paineis[nome].classList.toggle('visivel', aba.dataset.aba === nome);
      });
    });
  });

  document.querySelectorAll('form').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const dados = { aba: form.dataset.aba };
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = valor.trim ? valor.trim() : valor;
      });
      fetch('/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados),
      })
        .then(function (r) { return r.json(); })
        .then(function (resposta) {
          mostrarResposta(form, resposta);
        });
    });
  });

  function mostrarResposta(form, resposta) {
    const divErros = form.querySelector('.erros');
    if (resposta.erros.length > 0) {
      divErros.innerHTML = resposta.erros.map(function (erro) {
        return '<p>' + erro + '</p>';
      }).join('');
      divErros.classList.add('visivel');
      return;
    }
    document.querySelector('main').style.display = 'none';
    document.getElementById('oficio').textContent = resposta.oficio;
    document.getElementById('confirmacao').classList.remove('oculto');
  }

  configurarMascaraValor();
  configurarMascaraPadrao();
});

function configurarMascaraValor() {
  document.querySelectorAll('input[name="valor"]').forEach(function (campo) {
    campo.addEventListener('blur', function () {
      const digitos = campo.value.replace(/\D/g, '');
      if (!digitos) return;
      let centavos = digitos;
      while (centavos.length > 2 && centavos[0] === '0') {
        centavos = centavos.slice(1);
      }
      const numero = parseInt(centavos, 10) / 100;
      campo.value = 'R$ ' + numero.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    });
  });
}

function configurarMascaraPadrao() {
  const mascaras = {
    cpf: { tamanho: 11, grupos: [3, 3, 3, 2], separadores: ['.', '.', '-'] },
    cep: { tamanho: 8, grupos: [5, 3], separadores: ['-'] },
    nascimento: { tamanho: 8, grupos: [2, 2, 4], separadores: ['/', '/'] },
  };
  Object.keys(mascaras).forEach(function (nome) {
    document.querySelectorAll('input[name="' + nome + '"]').forEach(function (campo) {
      campo.addEventListener('blur', function () {
        const digitos = campo.value.replace(/\D/g, '');
        if (!digitos || digitos.length < mascaras[nome].tamanho) return;
        const limite = digitos.slice(0, mascaras[nome].tamanho);
        let resultado = '';
        let posicao = 0;
        for (let i = 0; i < mascaras[nome].grupos.length; i++) {
          if (i > 0) resultado += mascaras[nome].separadores[i - 1];
          resultado += limite.slice(posicao, posicao + mascaras[nome].grupos[i]);
          posicao += mascaras[nome].grupos[i];
        }
        campo.value = resultado;
      });
    });
  });
}
