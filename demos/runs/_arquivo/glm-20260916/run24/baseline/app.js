'use strict';

const CAMPOS_SOLICITANTE = [
  { id: 'nome_completo', rotulo: 'NOME COMPLETO - SEM ABREVIAR', placeholder: 'Maria Aparecida de Souza', largura: 2 },
  { id: 'n_usp', rotulo: 'N. USP', placeholder: '1234567' },
  { id: 'programa', rotulo: 'PROGRAMA', placeholder: 'Ciência da Computação' },
  { id: 'nivel', rotulo: 'NÍVEL', placeholder: 'Selecione', tipo: 'select', opcoes: ['Mestrado', 'Doutorado'], alunos: true },
  { id: 'tipo_auxilio', rotulo: 'TIPO DE AUXÍLIO', placeholder: 'Selecione', tipo: 'select', opcoes: ['Participação em evento', 'Banca de exame ou defesa', 'Outro'], alunos: true },
  { id: 'email', rotulo: 'E-MAIL', placeholder: 'maria.aparecida@usp.br', largura: 2 },
  { id: 'nome_evento', rotulo: 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', placeholder: 'SBBD 2025', largura: 2 },
  { id: 'periodo_evento', rotulo: 'PERÍODO DO EVENTO, EXAME OU DEFESA', placeholder: '13/10/2025 a 16/10/2025' },
  { id: 'cidade_evento', rotulo: 'CIDADE DO EVENTO, EXAME OU DEFESA', placeholder: 'Petrópolis' },
  { id: 'estado_evento', rotulo: 'ESTADO DO EVENTO, EXAME OU DEFESA', placeholder: 'RJ' },
  { id: 'pais_evento', rotulo: 'PAÍS DO EVENTO, EXAME OU DEFESA', placeholder: 'Brasil' },
  { id: 'link_evento', rotulo: 'LINK DO EVENTO, EXAME OU DEFESA', placeholder: 'https://sbbd.org.br' },
  { id: 'valor_solicitado', rotulo: 'VALOR SOLICITADO (R$)', placeholder: '150000', formato: 'moeda' },
  { id: 'detalhamento', rotulo: 'DETALHAMENTO DO PEDIDO', placeholder: 'Passagem aérea e inscrição no evento', tipo: 'textarea', largura: 2 },
  { id: 'apresentacao_trabalho', rotulo: 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', placeholder: 'Selecione', tipo: 'select', opcoes: ['Pôster', 'Apresentação oral', 'Outra', 'Não irá apresentar trabalho'], largura: 2 }
];

const CAMPOS_ENDERECO = [
  { id: 'data_nascimento', rotulo: 'DATA DE NASCIMENTO', placeholder: '01011980', formato: 'data' },
  { id: 'logradouro', rotulo: 'LOGRADOURO', placeholder: 'Rua do Anfiteatro' },
  { id: 'numero', rotulo: 'NÚMERO', placeholder: '155' },
  { id: 'complemento', rotulo: 'COMPLEMENTO', placeholder: 'Sala 12' },
  { id: 'bairro', rotulo: 'BAIRRO', placeholder: 'Butantã' },
  { id: 'cep', rotulo: 'CEP', placeholder: '05508090', formato: 'cep' },
  { id: 'cidade', rotulo: 'CIDADE', placeholder: 'São Paulo' },
  { id: 'estado', rotulo: 'ESTADO', placeholder: 'SP' }
];

const CAMPOS_PAGAMENTO = [
  { id: 'cpf', rotulo: 'CPF (SEPARADOS POR PONTOS E TRAÇO)', placeholder: '12345678909', formato: 'cpf' },
  { id: 'rg_rnm', rotulo: 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', placeholder: '12.345.678-9', largura: 2 },
  { id: 'nome_banco', rotulo: 'NOME DO BANCO', placeholder: 'Banco do Brasil' },
  { id: 'agencia', rotulo: 'NÚMERO DA AGÊNCIA', placeholder: '0326' },
  { id: 'numero_conta', rotulo: 'NÚMERO DA CONTA', placeholder: '12345-6' }
];

function aplicarMascara(valor, padrao) {
  const digitos = valor.replace(/\D/g, '');
  let saida = '';
  let i = 0;
  for (const caractere of padrao) {
    if (i >= digitos.length) break;
    saida += caractere === 'd' ? digitos[i++] : caractere;
  }
  return saida;
}

function formatarMoeda(valor) {
  const digitos = valor.replace(/\D/g, '').replace(/^0+(?=\d)/, '');
  if (!digitos) return '';
  const centavos = digitos.slice(-2).padStart(2, '0');
  const parteInteira = digitos.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return 'R$ ' + (parteInteira || '0') + ',' + centavos;
}

const FORMATADORES = {
  moeda: valor => formatarMoeda(valor),
  cpf: valor => aplicarMascara(valor, 'ddd.ddd.ddd-dd'),
  cep: valor => aplicarMascara(valor, 'ddddd-ddd'),
  data: valor => aplicarMascara(valor, 'dd/dd/dddd')
};

function campoHtml(campo) {
  const atributos = `id='${campo.id}' name='${campo.id}' placeholder='${campo.placeholder}'` + (campo.formato ? ` data-formato='${campo.formato}'` : '');
  let controle;
  if (campo.tipo === 'select') {
    const opcoes = [`<option value='' selected hidden>Selecione</option>`]
      .concat(campo.opcoes.map(opcao => `<option value='${opcao}'>${opcao}</option>`)).join('');
    controle = `<select ${atributos}>${opcoes}</select>`;
  } else if (campo.tipo === 'textarea') {
    controle = `<textarea ${atributos}></textarea>`;
  } else {
    controle = `<input type='text' ${atributos}>`;
  }
  const classe = campo.largura === 2 ? 'campo campo-largo' : 'campo';
  return `<div class='${classe}'><label for='${campo.id}'>${campo.rotulo}</label>${controle}</div>`;
}

function montarFormulario(idFormulario, tipo) {
  const form = document.getElementById(idFormulario);
  const campos = CAMPOS_SOLICITANTE.filter(campo => tipo === 'alunos' || !campo.alunos);
  form.innerHTML = `
    <div class='erros' hidden></div>
    <fieldset><legend>SOLICITANTE E EVENTO</legend><div class='grade'>${campos.map(campoHtml).join('')}</div></fieldset>
    <fieldset><legend>ENDEREÇO DO SOLICITANTE</legend><div class='grade'>${CAMPOS_ENDERECO.map(campoHtml).join('')}</div></fieldset>
    <fieldset><legend>INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO</legend><div class='grade'>${CAMPOS_PAGAMENTO.map(campoHtml).join('')}</div></fieldset>
    <button type='submit'>Enviar solicitação</button>`;
  form.addEventListener('submit', evento => {
    evento.preventDefault();
    enviar(form, tipo);
  });
  form.querySelectorAll('[data-formato]').forEach(elemento => {
    elemento.addEventListener('blur', () => {
      elemento.value = FORMATADORES[elemento.dataset.formato](elemento.value);
    });
  });
}

async function enviar(form, tipo) {
  const dados = { tipo: tipo };
  form.querySelectorAll('[name]').forEach(elemento => { dados[elemento.name] = elemento.value; });
  const resposta = await fetch('/api/solicitar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/' },
    body: JSON.stringify(dados)
  }).then(respostaHttp => respostaHttp.());
  const caixaErros = form.querySelector('.erros');
  if (resposta.erros && resposta.erros.length > 0) {
    caixaErros.innerHTML = resposta.erros.map(mensagem => '<div>' + mensagem + '</div>').join('');
    caixaErros.hidden = false;
    return;
  }
  document.getElementById('abas').hidden = true;
  document.getElementById('formularios').hidden = true;
  document.getElementById('oficio').textContent = resposta.oficio;
  document.getElementById('confirmacao').hidden = false;
}

montarFormulario('form-alunos', 'alunos');
montarFormulario('form-docentes', 'docentes');

document.querySelectorAll('.aba').forEach(aba => {
  aba.addEventListener('click', () => {
    document.querySelectorAll('.aba').forEach(outra => outra.classList.toggle('ativa', outra === aba));
    document.getElementById('form-alunos').hidden = aba.dataset.formulario !== 'alunos';
    document.getElementById('form-docentes').hidden = aba.dataset.formulario !== 'docentes';
  });
});
