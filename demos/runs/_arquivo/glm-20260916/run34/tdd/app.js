'use strict';

function soDigitos(texto) {
  return texto.replace(/\D/g, '');
}

function formatarMoeda(texto) {
  const digitos = soDigitos(texto).replace(/^0+(?=\d)/, '');
  if (!digitos) return '';
  const centavos = digitos.padStart(3, '0');
  const reais = centavos.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + reais + ',' + centavos.slice(-2);
}

function formatarCpf(texto) {
  const d = soDigitos(texto).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return d.slice(0, 3) + '.' + d.slice(3);
  if (d.length <= 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
  return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
}

function formatarCep(texto) {
  const d = soDigitos(texto).slice(0, 8);
  return d.length <= 5 ? d : d.slice(0, 5) + '-' + d.slice(5);
}

function formatarData(texto) {
  const d = soDigitos(texto).slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
  return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
}

for (const [seletor, formatar] of [
  ['.campo-moeda', formatarMoeda],
  ['.campo-cpf', formatarCpf],
  ['.campo-cep', formatarCep],
  ['.campo-data', formatarData],
]) {
  for (const campo of document.querySelectorAll(seletor)) {
    campo.addEventListener('blur', function () {
      campo.value = formatar(campo.value);
    });
  }
}

const abas = {
  alunos: {
    botao: document.getElementById('aba-alunos'),
    formulario: document.getElementById('form-alunos'),
  },
  docentes: {
    botao: document.getElementById('aba-docentes'),
    formulario: document.getElementById('form-docentes'),
  },
};

function abrirAba(nome) {
  for (const [chave, aba] of Object.entries(abas)) {
    const ativa = chave === nome;
    aba.botao.classList.toggle('ativa', ativa);
    aba.formulario.hidden = !ativa;
  }
}

abas.alunos.botao.addEventListener('click', function () { abrirAba('alunos'); });
abas.docentes.botao.addEventListener('click', function () { abrirAba('docentes'); });

for (const aba of Object.values(abas)) {
  aba.formulario.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    const areaErros = aba.formulario.querySelector('.erros');
    areaErros.hidden = true;
    areaErros.textContent = '';
    const dados = { aba: aba.formulario.dataset.aba };
    for (const [nome, valor] of new FormData(aba.formulario)) {
      dados[nome] = valor;
    }
    const resposta = await fetch('/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados),
    });
    const corpo = await resposta.();
    if (corpo.erros) {
      areaErros.textContent = corpo.erros.join('\n');
      areaErros.hidden = false;
      return;
    }
    document.getElementById('oficio').textContent = corpo.oficio;
    document.getElementById('solicitacao').hidden = true;
    document.getElementById('confirmacao').hidden = false;
  });
}
