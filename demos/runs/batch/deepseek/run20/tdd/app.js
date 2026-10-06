const CAMPOS = [
  [
    { id: 'nome', rotulo: 'NOME COMPLETO - SEM ABREVIAR', placeholder: 'Maria Silva Santos', largo: 2 },
    { id: 'n_usp', rotulo: 'N. USP', placeholder: '12345678', entrada: 'numerico' },
    { id: 'programa', rotulo: 'PROGRAMA', placeholder: 'Ciência da Computação', largo: 2 },
    { id: 'nivel', rotulo: 'NÍVEL', opcoes: ['Mestrado', 'Doutorado'], alunos: true },
    { id: 'tipo_auxilio', rotulo: 'TIPO DE AUXÍLIO', opcoes: ['Participação em evento', 'Banca de exame ou defesa', 'Outro'], alunos: true },
    { id: 'email', rotulo: 'E-MAIL', placeholder: 'maria@ime.usp.br', entrada: 'email' },
    { id: 'evento', rotulo: 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', placeholder: 'Simpósio Brasileiro de Computação', largo: 2 },
    { id: 'periodo', rotulo: 'PERÍODO DO EVENTO, EXAME OU DEFESA', placeholder: '10/10/2024 a 12/10/2024', largo: 2 },
    { id: 'cidade_evento', rotulo: 'CIDADE DO EVENTO, EXAME OU DEFESA', placeholder: 'São Paulo' },
    { id: 'estado_evento', rotulo: 'ESTADO DO EVENTO, EXAME OU DEFESA', placeholder: 'SP' },
    { id: 'pais_evento', rotulo: 'PAÍS DO EVENTO, EXAME OU DEFESA', placeholder: 'Brasil' },
    { id: 'link', rotulo: 'LINK DO EVENTO, EXAME OU DEFESA', placeholder: 'evento.usp.br', opcional: true, largo: 2 },
    { id: 'valor', rotulo: 'VALOR SOLICITADO (R$)', placeholder: '150000', formato: 'moeda' },
    { id: 'detalhamento', rotulo: 'DETALHAMENTO DO PEDIDO', placeholder: 'Passagem aérea e hospedagem.', longo: true, largo: 2 },
    { id: 'apresentacao', rotulo: 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', opcoes: ['Pôster', 'Apresentação oral', 'Outra', 'Não irá apresentar trabalho'], largo: 2 }
  ],
  [
    { id: 'nascimento', rotulo: 'DATA DE NASCIMENTO', placeholder: '01021980', formato: 'data' },
    { id: 'logradouro', rotulo: 'LOGRADOURO', placeholder: 'Rua do Matão', largo: 2 },
    { id: 'numero', rotulo: 'NÚMERO', placeholder: '1010' },
    { id: 'complemento', rotulo: 'COMPLEMENTO', placeholder: 'Bloco B', opcional: true },
    { id: 'bairro', rotulo: 'BAIRRO', placeholder: 'Butantã' },
    { id: 'cep', rotulo: 'CEP', placeholder: '05508090', formato: 'cep' },
    { id: 'cidade', rotulo: 'CIDADE', placeholder: 'São Paulo' },
    { id: 'estado', rotulo: 'ESTADO', placeholder: 'SP' }
  ],
  [
    { id: 'cpf', rotulo: 'CPF (SEPARADOS POR PONTOS E TRAÇO)', placeholder: '12345678909', formato: 'cpf' },
    { id: 'rg', rotulo: 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', placeholder: '12.345.678-9' },
    { id: 'banco', rotulo: 'NOME DO BANCO', placeholder: 'Banco do Brasil', largo: 2 },
    { id: 'agencia', rotulo: 'NÚMERO DA AGÊNCIA', placeholder: '1234', entrada: 'numerico' },
    { id: 'conta', rotulo: 'NÚMERO DA CONTA', placeholder: '56789-0' }
  ]
];

function criarCampo(item, aba) {
  const caixa = document.createElement('div');
  caixa.className = item.largo ? 'campo largo-' + item.largo : 'campo';
  const id = aba + '-' + item.id;
  const rotulo = document.createElement('label');
  rotulo.htmlFor = id;
  rotulo.textContent = item.rotulo;
  let controle;
  if (item.opcoes) {
    controle = document.createElement('select');
    const vazio = document.createElement('option');
    vazio.value = '';
    vazio.textContent = 'Selecione';
    controle.append(vazio);
    for (const opcao of item.opcoes) {
      const alternativa = document.createElement('option');
      alternativa.value = opcao;
      alternativa.textContent = opcao;
      controle.append(alternativa);
    }
  } else if (item.longo) {
    controle = document.createElement('textarea');
    controle.rows = 2;
    controle.placeholder = item.placeholder;
  } else {
    controle = document.createElement('input');
    controle.type = item.entrada === 'email' ? 'email' : 'text';
    controle.placeholder = item.placeholder;
    if (item.entrada === 'numerico') controle.inputMode = 'numeric';
  }
  controle.id = id;
  controle.name = item.id;
  if (item.formato) controle.dataset.formato = item.formato;
  caixa.append(rotulo, controle);
  return caixa;
}

function montarFormulario(painel) {
  const aba = painel.dataset.aba;
  const formulario = painel.querySelector('form');
  for (const grade of formulario.querySelectorAll('.grade')) {
    for (const item of CAMPOS[Number(grade.dataset.bloco)]) {
      if (item.alunos && aba !== 'ALUNOS') continue;
      grade.append(criarCampo(item, aba));
    }
  }
  formulario.addEventListener('submit', enviar);
  formulario.addEventListener('focusout', formatarCampo);
}

function somenteDigitos(valor) {
  return valor.replace(/\D/g, '');
}

function formatarCampo(evento) {
  const controle = evento.target;
  const formato = controle.dataset ? controle.dataset.formato : null;
  if (!formato) return;
  controle.value = formatar(formato, controle.value);
}

function formatar(formato, valor) {
  const digitos = somenteDigitos(valor);
  if (!digitos) return '';
  if (formato === 'moeda') {
    const centavos = parseInt(digitos, 10);
    const resto = String(centavos % 100).padStart(2, '0');
    return 'R$ ' + Math.floor(centavos / 100).toLocaleString('pt-BR') + ',' + resto;
  }
  if (formato === 'cpf') {
    const d = digitos.slice(0, 11);
    let saida = d.slice(0, 3);
    if (d.length > 3) saida += '.' + d.slice(3, 6);
    if (d.length > 6) saida += '.' + d.slice(6, 9);
    if (d.length > 9) saida += '-' + d.slice(9, 11);
    return saida;
  }
  if (formato === 'cep') {
    const d = digitos.slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }
  const d = digitos.slice(0, 8);
  let saida = d.slice(0, 2);
  if (d.length > 2) saida += '/' + d.slice(2, 4);
  if (d.length > 4) saida += '/' + d.slice(4, 8);
  return saida;
}

function mostrarErros(painel, erros) {
  const caixa = painel.querySelector('.erros');
  caixa.replaceChildren();
  for (const erro of erros) {
    const linha = document.createElement('p');
    linha.textContent = erro;
    caixa.append(linha);
  }
  caixa.hidden = false;
}

function mostrarConfirmacao(oficio) {
  document.querySelector('.abas').hidden = true;
  const principal = document.querySelector('main');
  principal.replaceChildren();
  const secao = document.createElement('section');
  secao.className = 'confirmacao';
  const titulo = document.createElement('h2');
  titulo.textContent = 'Solicitação registrada';
  const texto = document.createElement('pre');
  texto.className = 'oficio';
  texto.textContent = oficio;
  secao.append(titulo, texto);
  principal.append(secao);
}

async function enviar(evento) {
  evento.preventDefault();
  const formulario = evento.currentTarget;
  const painel = formulario.closest('.painel');
  const dados = { aba: formulario.dataset.aba };
  for (const controle of formulario.elements) {
    if (controle.name) dados[controle.name] = controle.value.trim();
  }
  const resposta = await fetch('/solicitar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados)
  });
  const resultado = await resposta.json();
  if (resultado.erros && resultado.erros.length) {
    mostrarErros(painel, resultado.erros);
    return;
  }
  mostrarConfirmacao(resultado.oficio);
}

function ativarAba(nome) {
  for (const botao of document.querySelectorAll('.aba')) {
    botao.classList.toggle('ativa', botao.dataset.aba === nome);
  }
  for (const painel of document.querySelectorAll('.painel')) {
    painel.classList.toggle('ativo', painel.dataset.aba === nome);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  for (const painel of document.querySelectorAll('.painel')) {
    montarFormulario(painel);
  }
  for (const botao of document.querySelectorAll('.aba')) {
    botao.addEventListener('click', () => ativarAba(botao.dataset.aba));
  }
  ativarAba('ALUNOS');
});
