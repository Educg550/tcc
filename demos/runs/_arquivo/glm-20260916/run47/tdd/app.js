'use strict';

function apenasDigitos(texto) {
  return String(texto).replace(/[^0-9]/g, '');
}

function agrupar(numero) {
  let texto = String(numero);
  let blocos = '';
  while (texto.length > 3) {
    blocos = '.' + texto.slice(-3) + blocos;
    texto = texto.slice(0, -3);
  }
  return texto + blocos;
}

function formatarMoeda(texto) {
  const centavos = parseInt(apenasDigitos(texto) || '0', 10);
  return 'R$ ' + agrupar(Math.floor(centavos / 100)) + ',' + String(centavos % 100).padStart(2, '0');
}

function formatarCpf(texto) {
  const d = apenasDigitos(texto);
  if (d.length !== 11) {
    return texto;
  }
  return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
}

function formatarCep(texto) {
  const d = apenasDigitos(texto);
  if (d.length !== 8) {
    return texto;
  }
  return d.slice(0, 5) + '-' + d.slice(5);
}

function formatarData(texto) {
  const d = apenasDigitos(texto);
  if (d.length !== 8) {
    return texto;
  }
  return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
}

const FORMATADORES = {
  valor_solicitado: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data_nascimento: formatarData
};

Object.keys(FORMATADORES).forEach(function (nome) {
  const formatar = FORMATADORES[nome];
  document.querySelectorAll('input[name="' + nome + '"]').forEach(function (campo) {
    campo.addEventListener('blur', function () {
      campo.value = formatar(campo.value);
    });
  });
});

const abas = Array.prototype.slice.call(document.querySelectorAll('.aba'));

function ativarAba(selecionada) {
  abas.forEach(function (aba) {
    const ligada = aba === selecionada;
    aba.classList.toggle('active', ligada);
    aba.setAttribute('aria-selected', ligada ? 'true' : 'false');
    document.getElementById('painel-' + aba.dataset.aba).hidden = !ligada;
  });
}

abas.forEach(function (aba) {
  aba.addEventListener('click', function () {
    ativarAba(aba);
    document.getElementById('confirmacao').hidden = true;
    document.getElementById('conteudo').hidden = false;
  });
});

function mostrarErros(form, mensagens) {
  const caixa = form.querySelector('.erros');
  caixa.textContent = '';
  mensagens.forEach(function (mensagem) {
    const paragrafo = document.createElement('p');
    paragrafo.textContent = mensagem;
    caixa.appendChild(paragrafo);
  });
  caixa.hidden = false;
}

document.querySelectorAll('.formulario').forEach(function (form) {
  form.addEventListener('submit', function (evento) {
    evento.preventDefault();
    const dados = { aba: form.dataset.aba };
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = valor;
    });
    fetch('/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados)
    })
      .then(function (resposta) {
        return resposta.();
      })
      .then(function (resultado) {
        if (resultado.erros && resultado.erros.length > 0) {
          mostrarErros(form, resultado.erros);
          return;
        }
        form.querySelector('.erros').hidden = true;
        document.getElementById('oficio').textContent = resultado.oficio;
        document.getElementById('conteudo').hidden = true;
        document.getElementById('confirmacao').hidden = false;
      });
  });
});
