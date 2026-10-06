'use strict';

const abas = document.querySelectorAll('.aba');
const formularios = document.querySelectorAll('form.formulario');

abas.forEach((aba) => {
  aba.addEventListener('click', () => {
    abas.forEach((outra) => outra.classList.toggle('ativa', outra === aba));
    formularios.forEach((formulario) => {
      formulario.hidden = formulario.id !== aba.dataset.alvo;
    });
  });
});

function soDigitos(valor) {
  return valor.replace(/\D/g, '');
}

function formatarMoeda(campo) {
  const digitos = soDigitos(campo.value);
  if (!digitos) {
    campo.value = '';
    return;
  }
  const centavos = digitos.padStart(3, '0');
  const reais = centavos.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  campo.value = 'R$ ' + reais + ',' + centavos.slice(-2);
}

function formatarCpf(campo) {
  const d = soDigitos(campo.value).slice(0, 11);
  let valor = d;
  if (d.length > 9) {
    valor = d.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2}).*/, '$1.$2.$3-$4');
  } else if (d.length > 6) {
    valor = d.replace(/(\d{3})(\d{3})(\d+).*/, '$1.$2.$3');
  } else if (d.length > 3) {
    valor = d.replace(/(\d{3})(\d+).*/, '$1.$2');
  }
  campo.value = valor;
}

function formatarCep(campo) {
  const d = soDigitos(campo.value).slice(0, 8);
  campo.value = d.length > 5 ? d.replace(/(\d{5})(\d+).*/, '$1-$2') : d;
}

function formatarData(campo) {
  const d = soDigitos(campo.value).slice(0, 8);
  let valor = d;
  if (d.length > 4) {
    valor = d.replace(/(\d{2})(\d{2})(\d+).*/, '$1/$2/$3');
  } else if (d.length > 2) {
    valor = d.replace(/(\d{2})(\d+).*/, '$1/$2');
  }
  campo.value = valor;
}

const formatadores = {
  valor_solicitado: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data_de_nascimento: formatarData,
};

Object.entries(formatadores).forEach(([nome, formatar]) => {
  document.querySelectorAll('[name="' + nome + '"]').forEach((campo) => {
    campo.addEventListener('blur', () => formatar(campo));
  });
});

formularios.forEach((formulario) => {
  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const dados = {};
    new FormData(formulario).forEach((valor, chave) => {
      dados[chave] = valor;
    });
    const resposta = await fetch('/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados),
    });
    const retorno = await resposta.();
    const aviso = formulario.querySelector('.erros');
    if (!retorno.ok) {
      aviso.replaceChildren(...retorno.erros.map((mensagem) => {
        const p = document.createElement('p');
        p.textContent = mensagem;
        return p;
      }));
      aviso.hidden = false;
      return;
    }
    aviso.hidden = true;
    document.getElementById('formularios').hidden = true;
    document.getElementById('oficio').textContent = retorno.oficio;
    document.getElementById('confirmacao').hidden = false;
  });
});
