"use strict";

const OPCOES = {
  nivel: ["Mestrado", "Doutorado"],
  tipo_auxilio: ["Participação em evento", "Banca de exame ou defesa", "Outro"],
  apresentacao: ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"],
};

const SOLICITANTE_ALUNOS = [
  { id: "nome", rotulo: "NOME COMPLETO - SEM ABREVIAR", span: 5, exemplo: "Maria de Souza Silva" },
  { id: "nusp", rotulo: "N. USP", span: 2, exemplo: "8765432", digitos: true },
  { id: "programa", rotulo: "PROGRAMA", span: 5, exemplo: "Ciência da Computação" },
  { id: "nivel", rotulo: "NÍVEL", span: 3, opcoes: OPCOES.nivel },
  { id: "tipo_auxilio", rotulo: "TIPO DE AUXÍLIO", span: 6, opcoes: OPCOES.tipo_auxilio },
  { id: "email", rotulo: "E-MAIL", span: 3, exemplo: "maria.silva@usp.br" },
  { id: "evento", rotulo: "NOME DO EVENTO / BANCA DE EXAME OU DEFESA", span: 6, exemplo: "Congresso da SBC" },
  { id: "periodo", rotulo: "PERÍODO DO EVENTO, EXAME OU DEFESA", span: 6, exemplo: "21 a 24 de julho de 2025" },
  { id: "cidade_evento", rotulo: "CIDADE DO EVENTO, EXAME OU DEFESA", span: 3, exemplo: "São Paulo" },
  { id: "estado_evento", rotulo: "ESTADO DO EVENTO, EXAME OU DEFESA", span: 2, exemplo: "SP" },
  { id: "pais_evento", rotulo: "PAÍS DO EVENTO, EXAME OU DEFESA", span: 3, exemplo: "Brasil" },
  { id: "link_evento", rotulo: "LINK DO EVENTO, EXAME OU DEFESA", span: 4, exemplo: "https://evento.org.br" },
  { id: "valor", rotulo: "VALOR SOLICITADO (R$)", span: 4, exemplo: "150000", digitos: true, formato: "moeda" },
  { id: "apresentacao", rotulo: "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", span: 8, opcoes: OPCOES.apresentacao },
  { id: "detalhamento", rotulo: "DETALHAMENTO DO PEDIDO", span: 12, exemplo: "Passagem aérea de ida e volta e inscrição no evento", longo: true },
];

const SOLICITANTE_DOCENTES = [
  { id: "nome", rotulo: "NOME COMPLETO - SEM ABREVIAR", span: 5, exemplo: "Carlos Eduardo Lima" },
  { id: "nusp", rotulo: "N. USP", span: 2, exemplo: "1234568", digitos: true },
  { id: "programa", rotulo: "PROGRAMA", span: 5, exemplo: "Estatística" },
  { id: "email", rotulo: "E-MAIL", span: 4, exemplo: "carlos.lima@ime.usp.br" },
  { id: "evento", rotulo: "NOME DO EVENTO / BANCA DE EXAME OU DEFESA", span: 8, exemplo: "Banca de defesa de mestrado" },
  { id: "periodo", rotulo: "PERÍODO DO EVENTO, EXAME OU DEFESA", span: 6, exemplo: "03 de setembro de 2025" },
  { id: "cidade_evento", rotulo: "CIDADE DO EVENTO, EXAME OU DEFESA", span: 3, exemplo: "São Paulo" },
  { id: "estado_evento", rotulo: "ESTADO DO EVENTO, EXAME OU DEFESA", span: 3, exemplo: "SP" },
  { id: "pais_evento", rotulo: "PAÍS DO EVENTO, EXAME OU DEFESA", span: 4, exemplo: "Brasil" },
  { id: "link_evento", rotulo: "LINK DO EVENTO, EXAME OU DEFESA", span: 4, exemplo: "https://eventos.org.br" },
  { id: "valor", rotulo: "VALOR SOLICITADO (R$)", span: 4, exemplo: "250000", digitos: true, formato: "moeda" },
  { id: "apresentacao", rotulo: "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", span: 12, opcoes: OPCOES.apresentacao },
  { id: "detalhamento", rotulo: "DETALHAMENTO DO PEDIDO", span: 12, exemplo: "Diárias de hospedagem e transporte para a banca examinadora", longo: true },
];

const ENDERECO = [
  { id: "data_nascimento", rotulo: "DATA DE NASCIMENTO", span: 2, exemplo: "01021980", digitos: true, formato: "data" },
  { id: "logradouro", rotulo: "LOGRADOURO", span: 4, exemplo: "Rua do Matão" },
  { id: "numero", rotulo: "NÚMERO", span: 1, exemplo: "1010" },
  { id: "complemento", rotulo: "COMPLEMENTO", span: 2, exemplo: "Sala 214A" },
  { id: "bairro", rotulo: "BAIRRO", span: 3, exemplo: "Cidade Universitária" },
  { id: "cep", rotulo: "CEP", span: 3, exemplo: "05508090", digitos: true, formato: "cep" },
  { id: "cidade", rotulo: "CIDADE", span: 5, exemplo: "São Paulo" },
  { id: "estado", rotulo: "ESTADO", span: 4, exemplo: "SP" },
];

const PAGAMENTO = [
  { id: "cpf", rotulo: "CPF (SEPARADOS POR PONTOS E TRAÇO)", span: 2, exemplo: "12345678909", digitos: true, formato: "cpf" },
  { id: "rg_rnm", rotulo: "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", span: 2, exemplo: "10.234.567-8" },
  { id: "nome_banco", rotulo: "NOME DO BANCO", span: 3, exemplo: "Banco do Brasil" },
  { id: "agencia", rotulo: "NÚMERO DA AGÊNCIA", span: 1, exemplo: "0033", digitos: true },
  { id: "conta", rotulo: "NÚMERO DA CONTA", span: 4, exemplo: "12345-6" },
];

const BLOCOS = {
  alunos: [
    ["SOLICITANTE E EVENTO", SOLICITANTE_ALUNOS],
    ["ENDEREÇO DO SOLICITANTE", ENDERECO],
    ["INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO", PAGAMENTO],
  ],
  docentes: [
    ["SOLICITANTE E EVENTO", SOLICITANTE_DOCENTES],
    ["ENDEREÇO DO SOLICITANTE", ENDERECO],
    ["INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO", PAGAMENTO],
  ],
};

const MOLDES = { cpf: "###.###.###-##", cep: "#####-###", data: "##/##/####" };

function soDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function moeda(digitos) {
  const valor = Number(digitos);
  const reais = Math.trunc(valor / 100).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const centavos = String(valor % 100).padStart(2, "0");
  return `R$ ${reais},${centavos}`;
}

function mascarar(digitos, molde) {
  let saida = "";
  let i = 0;
  for (const caractere of molde) {
    if (i >= digitos.length) break;
    saida += caractere === "#" ? digitos[i++] : caractere;
  }
  return saida;
}

function criarCampo(def, aba) {
  const campo = document.createElement("div");
  campo.className = "campo";
  campo.style.gridColumn = `span ${def.span}`;
  const rotulo = document.createElement("label");
  rotulo.textContent = def.rotulo;
  rotulo.htmlFor = `f-${aba}-${def.id}`;
  campo.appendChild(rotulo);
  let controle;
  if (def.opcoes) {
    controle = document.createElement("select");
    for (const opcao of ["", ...def.opcoes]) {
      const item = document.createElement("option");
      item.value = opcao;
      item.textContent = opcao === "" ? "Selecione" : opcao;
      controle.appendChild(item);
    }
  } else if (def.longo) {
    controle = document.createElement("textarea");
    controle.rows = 2;
    controle.placeholder = def.exemplo;
  } else {
    controle = document.createElement("input");
    controle.type = "text";
    controle.placeholder = def.exemplo;
  }
  controle.id = `f-${aba}-${def.id}`;
  if (def.digitos) {
    controle.inputMode = "numeric";
  }
  if (def.formato) {
    controle.addEventListener("blur", () => {
      const digitos = soDigitos(controle.value);
      controle.value = def.formato === "moeda"
        ? (digitos ? moeda(digitos) : "")
        : mascarar(digitos, MOLDES[def.formato]);
    });
  }
  campo.appendChild(controle);
  return campo;
}

function criarBloco(titulo, campos, aba) {
  const bloco = document.createElement("section");
  bloco.className = "bloco";
  const tituloBloco = document.createElement("h3");
  tituloBloco.textContent = titulo;
  bloco.appendChild(tituloBloco);
  const grade = document.createElement("div");
  grade.className = "grade";
  for (const def of campos) {
    grade.appendChild(criarCampo(def, aba));
  }
  bloco.appendChild(grade);
  return bloco;
}

function selecionarAba(aba) {
  for (const outra of ["alunos", "docentes"]) {
    document.getElementById(`aba-${outra}`).classList.toggle("ativa", outra === aba);
    document.getElementById(`form-${outra}`).classList.toggle("oculta", outra !== aba);
  }
}

async function enviar(aba) {
  const dados = { aba: aba };
  for (const [, campos] of BLOCOS[aba]) {
    for (const def of campos) {
      dados[def.id] = document.getElementById(`f-${aba}-${def.id}`).value;
    }
  }
  const resposta = await fetch("/solicitar", {
    method: "POST",
    headers: { "Content-Type": "application/" },
    body: JSON.stringify(dados),
  });
  const corpo = await resposta.();
  if (corpo.oficio !== null) {
    document.getElementById("oficio").textContent = corpo.oficio;
    document.getElementById("formulario").classList.add("oculta");
    document.getElementById("confirmacao").classList.remove("oculta");
    return;
  }
  const caixa = document.querySelector(`#form-${aba} .erros`);
  const mensagens = corpo.erros.map((msg) => {
    const paragrafo = document.createElement("p");
    paragrafo.textContent = msg;
    return paragrafo;
  });
  caixa.replaceChildren(...mensagens);
  caixa.classList.remove("oculta");
}

for (const aba of ["alunos", "docentes"]) {
  const form = document.getElementById(`form-${aba}`);
  const caixa = document.createElement("div");
  caixa.className = "erros oculta";
  form.appendChild(caixa);
  for (const [titulo, campos] of BLOCOS[aba]) {
    form.appendChild(criarBloco(titulo, campos, aba));
  }
  const botao = document.createElement("button");
  botao.type = "submit";
  botao.className = "enviar";
  botao.textContent = "Enviar solicitação";
  form.appendChild(botao);
  form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    enviar(aba);
  });
  document.getElementById(`aba-${aba}`).addEventListener("click", () => selecionarAba(aba));
}
