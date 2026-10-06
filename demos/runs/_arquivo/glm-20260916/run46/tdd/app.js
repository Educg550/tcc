function soDigitos(texto) {
  return texto.replace(/\D/g, '');
}

function formatarMoeda(campo) {
  const digitos = soDigitos(campo.value).replace(/^0+(?=\d)/, '');
  if (!digitos) {
    campo.value = '';
    return;
  }
  const centavos = digitos.slice(-2).padStart(2, '0');
  const reais = (digitos.slice(0, -2) || '0').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  campo.value = 'R$ ' + reais + ',' + centavos;
}

function formatarCpf(campo) {
  let digitos = soDigitos(campo.value).slice(0, 11);
  if (digitos.length > 3) {
    digitos = digitos.replace(/^(\d{3})(\d+)/, '$1.$2');
  }
  if (digitos.length > 7) {
    digitos = digitos.replace(/^(\d{3})\.(\d{3})(\d+)/, '$1.$2.$3');
  }
  if (digitos.length > 10) {
    digitos = digitos.replace(/^(\d{3})\.(\d{3})\.(\d{3})(\d+)/, '$1.$2.$3-$4');
  }
  campo.value = digitos;
}

function formatarCep(campo) {
  const digitos = soDigitos(campo.value).slice(0, 8);
  campo.value = digitos.length > 5 ? digitos.replace(/^(\d{5})(\d+)/, '$1-$2') : digitos;
}

function formatarData(campo) {
  let digitos = soDigitos(campo.value).slice(0, 8);
  if (digitos.length > 4) {
    digitos = digitos.replace(/^(\d{2})(\d{2})(\d+)/, '$1/$2/$3');
  } else if (digitos.length > 2) {
    digitos = digitos.replace(/^(\d{2})(\d+)/, '$1/$2');
  }
  campo.value = digitos;
}

const FORMATADORES = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData,
};

function configurarFormatacao() {
  document.querySelectorAll('[data-formato]').forEach((campo) => {
    campo.addEventListener('blur', () => FORMATADORES[campo.dataset.formato](campo));
  });
}

function configurarAbas() {
  const abas = document.querySelectorAll('.aba');
  abas.forEach((aba) => {
    aba.addEventListener('click', () => {
      abas.forEach((outra) => outra.classList.toggle('ativa', outra === aba));
      document.querySelectorAll('.formulario').forEach((formulario) => {
        formulario.hidden = formulario.dataset.aba !== aba.dataset.aba;
      });
    });
  });
}

function coletarCampos(formulario) {
  const campos = {};
  formulario.querySelectorAll('[data-rotulo]').forEach((campo) => {
    const valor = campo.dataset.formato === 'moeda' ? soDigitos(campo.value) : campo.value;
    campos[campo.dataset.rotulo] = valor;
  });
  return campos;
}

async function enviarFormulario(evento) {
  evento.preventDefault();
  const formulario = evento.target;
  const resposta = await fetch('/solicitacao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/' },
    body: JSON.stringify({ aba: formulario.dataset.aba, campos: coletarCampos(formulario) }),
  });
  const dados = await resposta.();
  const caixaErros = formulario.querySelector('.erros');
  if (resposta.ok) {
    caixaErros.hidden = true;
    document.getElementById('oficio').textContent = dados.oficio;
    document.getElementById('formularios').hidden = true;
    document.getElementById('confirmacao').hidden = false;
    window.scrollTo(0, 0);
  } else {
    caixaErros.replaceChildren(
      ...dados.erros.map((mensagem) => {
        const paragrafo = document.createElement('p');
        paragrafo.textContent = mensagem;
        return paragrafo;
      })
    );
    caixaErros.hidden = false;
  }
}

configurarAbas();
configurarFormatacao();
document.querySelectorAll('form.formulario').forEach((formulario) => {
  formulario.addEventListener('submit', enviarFormulario);
});
