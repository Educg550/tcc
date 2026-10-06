'use strict';

const digitos = (valor) => valor.replace(/\D/g, '');

function moeda(centavos) {
  const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + reais + ',' + String(centavos % 100).padStart(2, '0');
}

function formatarMoeda(campo) {
  const d = digitos(campo.value);
  campo.value = d ? moeda(Number(d)) : '';
}

function formatarCpf(campo) {
  const d = digitos(campo.value);
  if (d.length === 11) {
    campo.value = d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  }
}

function formatarCep(campo) {
  const d = digitos(campo.value);
  if (d.length === 8) {
    campo.value = d.slice(0, 5) + '-' + d.slice(5);
  }
}

function formatarData(campo) {
  const d = digitos(campo.value);
  if (d.length === 8) {
    campo.value = d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  }
}

function ativarAba(nome) {
  for (const id of ['alunos', 'docentes']) {
    const aba = document.getElementById('aba-' + id);
    aba.classList.toggle('ativa', id === nome);
    aba.setAttribute('aria-selected', String(id === nome));
    document.getElementById('form-' + id).classList.toggle('oculto', id !== nome);
  }
}

document.getElementById('aba-alunos').addEventListener('click', () => ativarAba('alunos'));
document.getElementById('aba-docentes').addEventListener('click', () => ativarAba('docentes'));

for (const form of document.querySelectorAll('.formulario')) {
  form.querySelector('[name=valor]').addEventListener('blur', (e) => formatarMoeda(e.target));
  form.querySelector('[name=cpf]').addEventListener('blur', (e) => formatarCpf(e.target));
  form.querySelector('[name=cep]').addEventListener('blur', (e) => formatarCep(e.target));
  form.querySelector('[name=data_nascimento]').addEventListener('blur', (e) => formatarData(e.target));

  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const dados = Object.fromEntries(new FormData(form).entries());
    dados.tipo = form.dataset.tipo;
    const resposta = await fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(dados)
    });
    const resultado = await resposta.();
    if (resultado.ok) {
      document.getElementById('conteudo').classList.add('oculto');
      document.getElementById('oficio').textContent = resultado.oficio;
      document.getElementById('confirmacao').classList.remove('oculto');
      window.scrollTo(0, 0);
    } else {
      const caixa = form.querySelector('.erros');
      caixa.replaceChildren();
      for (const mensagem of resultado.erros) {
        const linha = document.createElement('p');
        linha.textContent = mensagem;
        caixa.append(linha);
      }
      caixa.classList.remove('oculto');
    }
  });
}
