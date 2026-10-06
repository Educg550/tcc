"use strict";

const MASCARAS = {
  valor: mascararValor,
  cpf: mascararCpf,
  cep: mascararCep,
  data: mascararData,
};

const BLOCOS = [
  {
    titulo: "SOLICITANTE E EVENTO",
    linhas: [
      [
        { chave: "nome_completo", rotulo: "NOME COMPLETO - SEM ABREVIAR", exemplo: "Ex.: Maria Aparecida de Souza", span: 5 },
        { chave: "n_usp", rotulo: "N. USP", exemplo: "Ex.: 8765432", span: 2 },
        { chave: "programa", rotulo: "PROGRAMA", exemplo: "Ex.: Ciência da Computação", span: 3 },
        { chave: "nivel", rotulo: "NÍVEL", exemplo: "Ex.: Mestrado", span: 2, alunos: true, opcoes: ["Mestrado", "Doutorado"] },
      ],
      [
        { chave: "tipo_auxilio", rotulo: "TIPO DE AUXÍLIO", exemplo: "Ex.: Participação em evento", span: 3, alunos: true, opcoes: ["Participação em evento", "Banca de exame ou defesa", "Outro"] },
        { chave: "email", rotulo: "E-MAIL", exemplo: "Ex.: maria.souza@usp.br", span: 4, tipo: "email" },
        { chave: "nome_evento", rotulo: "NOME DO EVENTO / BANCA DE EXAME OU DEFESA", exemplo: "Ex.: Congresso da SBC 2025", span: 5 },
      ],
      [
        { chave: "periodo_evento", rotulo: "PERÍODO DO EVENTO, EXAME OU DEFESA", exemplo: "Ex.: 10 a 12 de setembro de 2025", span: 2 },
        { chave: "cidade_evento", rotulo: "CIDADE DO EVENTO, EXAME OU DEFESA", exemplo: "Ex.: São Paulo", span: 3 },
        { chave: "estado_evento", rotulo: "ESTADO DO EVENTO, EXAME OU DEFESA", exemplo: "Ex.: SP", span: 2 },
        { chave: "pais_evento", rotulo: "PAÍS DO EVENTO, EXAME OU DEFESA", exemplo: "Ex.: Brasil", span: 2 },
        { chave: "link_evento", rotulo: "LINK DO EVENTO, EXAME OU DEFESA", exemplo: "Ex.: https://sbc.org.br/evento", span: 3 },
      ],
      [
        { chave: "valor_solicitado", rotulo: "VALOR SOLICITADO (R$)", exemplo: "Ex.: 150000", span: 2, mask: "valor" },
        { chave: "detalhamento", rotulo: "DETALHAMENTO DO PEDIDO", exemplo: "Ex.: Inscrição no evento e passagem aérea de ida e volta", span: 7, linhas: 2 },
        { chave: "apresentacao_trabalho", rotulo: "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", exemplo: "Ex.: Pôster", span: 3, opcoes: ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"] },
      ],
    ],
  },
  {
    titulo: "ENDEREÇO DO SOLICITANTE",
    linhas: [
      [
        { chave: "data_nascimento", rotulo: "DATA DE NASCIMENTO", exemplo: "Ex.: 01021980", span: 2, mask: "data" },
        { chave: "logradouro", rotulo: "LOGRADOURO", exemplo: "Ex.: Rua do Matão, 1010", span: 4 },
        { chave: "numero", rotulo: "NÚMERO", exemplo: "Ex.: 1010", span: 2 },
        { chave: "complemento", rotulo: "COMPLEMENTO", exemplo: "Ex.: Sala 234", span: 4 },
      ],
      [
        { chave: "bairro", rotulo: "BAIRRO", exemplo: "Ex.: Cidade Universitária", span: 4 },
        { chave: "cep", rotulo: "CEP", exemplo: "Ex.: 05508090", span: 2, mask: "cep" },
        { chave: "cidade", rotulo: "CIDADE", exemplo: "Ex.: São Paulo", span: 3 },
        { chave: "estado", rotulo: "ESTADO", exemplo: "Ex.: SP", span: 3 },
      ],
    ],
  },
  {
    titulo: "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    linhas: [
      [
        { chave: "cpf", rotulo: "CPF (SEPARADOS POR PONTOS E TRAÇO)", exemplo: "Ex.: 12345678909", span: 3, mask: "cpf" },
        { chave: "rg_rnm", rotulo: "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", exemplo: "Ex.: 12.345.678-9", span: 3 },
        { chave: "nome_banco", rotulo: "NOME DO BANCO", exemplo: "Ex.: Banco do Brasil", span: 2 },
        { chave: "agencia", rotulo: "NÚMERO DA AGÊNCIA", exemplo: "Ex.: 1234", span: 2 },
        { chave: "conta", rotulo: "NÚMERO DA CONTA", exemplo: "Ex.: 12345-6", span: 2 },
      ],
    ],
  },
];

const estado = { alunos: {}, docentes: {} };
let abaAtual = null;

function soDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function mascararValor(campo) {
  const d = soDigitos(campo.value);
  if (!d) {
    campo.value = "";
    return;
  }
  const milhar = (d.slice(0, -2) || "0").replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  campo.value = `R$ ${milhar},${d.slice(-2).padStart(2, "0")}`;
}

function mascararCpf(campo) {
  const d = soDigitos(campo.value).slice(0, 11);
  let valor = d.slice(0, 3);
  if (d.length > 3) valor += "." + d.slice(3, 6);
  if (d.length > 6) valor += "." + d.slice(6, 9);
  if (d.length > 9) valor += "-" + d.slice(9);
  campo.value = valor;
}

function mascararCep(campo) {
  const d = soDigitos(campo.value).slice(0, 8);
  campo.value = d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
}

function mascararData(campo) {
  const d = soDigitos(campo.value).slice(0, 8);
  let valor = d.slice(0, 2);
  if (d.length > 2) valor += "/" + d.slice(2, 4);
  if (d.length > 4) valor += "/" + d.slice(4);
  campo.value = valor;
}

function criarCampo(definicao, tipo) {
  const id = `${tipo}-${definicao.chave}`;
  const div = document.createElement("div");
  div.className = `campo span-${definicao.span}`;

  const label = document.createElement("label");
  label.htmlFor = id;
  label.textContent = definicao.rotulo;
  div.appendChild(label);

  let controle;
  if (definicao.opcoes) {
    controle = document.createElement("select");
    const vazia = document.createElement("option");
    vazia.value = "";
    vazia.textContent = definicao.exemplo;
    controle.appendChild(vazia);
    for (const texto of definicao.opcoes) {
      const opcao = document.createElement("option");
      opcao.value = texto;
      opcao.textContent = texto;
      controle.appendChild(opcao);
    }
  } else if (definicao.linhas) {
    controle = document.createElement("textarea");
    controle.rows = definicao.linhas;
    controle.placeholder = definicao.exemplo;
  } else {
    controle = document.createElement("input");
    controle.type = definicao.tipo || "text";
    controle.placeholder = definicao.exemplo;
  }
  controle.id = id;
  controle.name = definicao.chave;
  if (definicao.mask) {
    controle.dataset.mask = definicao.mask;
    controle.addEventListener("blur", () => MASCARAS[definicao.mask](controle));
  }
  div.appendChild(controle);
  return div;
}

function renderFormulario(tipo) {
  const form = document.getElementById("form-solicitacao");
  form.replaceChildren();

  const caixaErros = document.createElement("div");
  caixaErros.className = "erros";
  caixaErros.hidden = true;
  form.appendChild(caixaErros);

  for (const bloco of BLOCOS) {
    const secao = document.createElement("section");
    secao.className = "bloco";
    const titulo = document.createElement("h2");
    titulo.textContent = bloco.titulo;
    secao.appendChild(titulo);
    for (const linha of bloco.linhas) {
      const divLinha = document.createElement("div");
      divLinha.className = "linha";
      for (const definicao of linha) {
        if (definicao.alunos && tipo !== "alunos") continue;
        divLinha.appendChild(criarCampo(definicao, tipo));
      }
      secao.appendChild(divLinha);
    }
    form.appendChild(secao);
  }

  const botao = document.createElement("button");
  botao.type = "submit";
  botao.className = "enviar";
  botao.textContent = "Enviar solicitação";
  form.appendChild(botao);

  for (const [chave, valor] of Object.entries(estado[tipo])) {
    if (form.elements[chave]) form.elements[chave].value = valor;
  }
}

function salvarEstado() {
  const dados = {};
  for (const campo of document.getElementById("form-solicitacao").elements) {
    if (campo.name) dados[campo.name] = campo.value;
  }
  estado[abaAtual] = dados;
}

function abrirAba(tipo) {
  if (tipo === abaAtual) return;
  if (abaAtual) salvarEstado();
  abaAtual = tipo;
  renderFormulario(tipo);
  for (const nome of ["alunos", "docentes"]) {
    const botao = document.getElementById(`aba-${nome}`);
    botao.classList.toggle("ativa", nome === tipo);
    botao.setAttribute("aria-selected", nome === tipo ? "true" : "false");
  }
  document.getElementById("form-solicitacao").setAttribute("aria-labelledby", `aba-${tipo}`);
}

async function enviarSolicitacao(evento) {
  evento.preventDefault();
  const form = evento.target;
  form.querySelectorAll("[data-mask]").forEach((campo) => MASCARAS[campo.dataset.mask](campo));

  const campos = {};
  for (const campo of form.elements) {
    if (campo.name) campos[campo.name] = campo.value.trim();
  }

  const resposta = await fetch("/api/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/" },
    body: JSON.stringify({ tipo: abaAtual, campos }),
  });
  const dados = await resposta.();

  const caixa = form.querySelector(".erros");
  if (dados.erros && dados.erros.length > 0) {
    caixa.replaceChildren(
      ...dados.erros.map((mensagem) => {
        const item = document.createElement("div");
        item.textContent = mensagem;
        return item;
      })
    );
    caixa.hidden = false;
    return;
  }

  document.getElementById("oficio").textContent = dados.oficio;
  document.getElementById("formulario").hidden = true;
  document.getElementById("confirmacao").hidden = false;
  window.scrollTo(0, 0);
}

document.getElementById("aba-alunos").addEventListener("click", () => abrirAba("alunos"));
document.getElementById("aba-docentes").addEventListener("click", () => abrirAba("docentes"));
document.getElementById("form-solicitacao").addEventListener("submit", enviarSolicitacao);
abrirAba("alunos");
