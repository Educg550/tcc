"use strict";

const BLOCOS = [
  {
    titulo: "SOLICITANTE E EVENTO",
    campos: [
      { nome: "nome", rotulo: "NOME COMPLETO - SEM ABREVIAR", exemplo: "Maria Aparecida de Souza Oliveira", largura: 6 },
      { nome: "nusp", rotulo: "N. USP", exemplo: "8765432", largura: 2 },
      { nome: "programa", rotulo: "PROGRAMA", exemplo: "Ciência da Computação", largura: 4 },
      { nome: "nivel", rotulo: "NÍVEL", opcoes: ["Mestrado", "Doutorado"], exemplo: "Selecione o nível", largura: 3, somente: "alunos" },
      { nome: "tipo_auxilio", rotulo: "TIPO DE AUXÍLIO", opcoes: ["Participação em evento", "Banca de exame ou defesa", "Outro"], exemplo: "Selecione o tipo de auxílio", largura: 3, somente: "alunos" },
      { nome: "email", rotulo: "E-MAIL", tipo: "email", exemplo: "maria.souza@usp.br", largura: 6 },
      { nome: "evento", rotulo: "NOME DO EVENTO / BANCA DE EXAME OU DEFESA", exemplo: "Congresso Brasileiro de Matemática Aplicada", largura: 6 },
      { nome: "periodo", rotulo: "PERÍODO DO EVENTO, EXAME OU DEFESA", exemplo: "12 a 15 de outubro de 2025", largura: 6 },
      { nome: "cidade_evento", rotulo: "CIDADE DO EVENTO, EXAME OU DEFESA", exemplo: "Rio de Janeiro", largura: 3 },
      { nome: "estado_evento", rotulo: "ESTADO DO EVENTO, EXAME OU DEFESA", exemplo: "Rio de Janeiro", largura: 3 },
      { nome: "pais_evento", rotulo: "PAÍS DO EVENTO, EXAME OU DEFESA", exemplo: "Brasil", largura: 3 },
      { nome: "link_evento", rotulo: "LINK DO EVENTO, EXAME OU DEFESA", exemplo: "https://www.evento.com.br/2025", largura: 3 },
      { nome: "valor", rotulo: "VALOR SOLICITADO (R$)", exemplo: "R$ 1.500,00", largura: 3, formatar: "moeda" },
      { nome: "detalhamento", rotulo: "DETALHAMENTO DO PEDIDO", exemplo: "Passagem aérea de ida e volta e inscrição no evento", largura: 9, tipo: "textarea" },
      { nome: "apresentacao", rotulo: "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", opcoes: ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"], exemplo: "Selecione uma opção", largura: 6 }
    ]
  },
  {
    titulo: "ENDEREÇO DO SOLICITANTE",
    campos: [
      { nome: "data_nascimento", rotulo: "DATA DE NASCIMENTO", exemplo: "01/02/1980", largura: 3, formatar: "data" },
      { nome: "logradouro", rotulo: "LOGRADOURO", exemplo: "Rua do Anfiteatro", largura: 4 },
      { nome: "numero", rotulo: "NÚMERO", exemplo: "181", largura: 2 },
      { nome: "complemento", rotulo: "COMPLEMENTO", exemplo: "Bloco C, sala 214", largura: 3 },
      { nome: "bairro", rotulo: "BAIRRO", exemplo: "Butantã", largura: 3 },
      { nome: "cep", rotulo: "CEP", exemplo: "05508-090", largura: 3, formatar: "cep" },
      { nome: "cidade", rotulo: "CIDADE", exemplo: "São Paulo", largura: 3 },
      { nome: "estado", rotulo: "ESTADO", exemplo: "São Paulo", largura: 3 }
    ]
  },
  {
    titulo: "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    campos: [
      { nome: "cpf", rotulo: "CPF (SEPARADOS POR PONTOS E TRAÇO)", exemplo: "529.982.247-25", largura: 3, formatar: "cpf" },
      { nome: "rg_rnm", rotulo: "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", exemplo: "10.222.333-4", largura: 4 },
      { nome: "banco", rotulo: "NOME DO BANCO", exemplo: "Banco do Brasil", largura: 5 },
      { nome: "agencia", rotulo: "NÚMERO DA AGÊNCIA", exemplo: "0183", largura: 3 },
      { nome: "conta", rotulo: "NÚMERO DA CONTA", exemplo: "45678-9", largura: 4 }
    ]
  }
];

const NOMES_DE_CAMPO = BLOCOS.flatMap(function (bloco) {
  return bloco.campos.map(function (campo) { return campo.nome; });
});

const FORMATADORES = {
  moeda: function (valor) {
    const digitos = apenasDigitos(valor);
    if (!digitos) {
      return "";
    }
    const centavos = parseInt(digitos, 10);
    const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + reais + "," + String(centavos % 100).padStart(2, "0");
  },
  cpf: function (valor) {
    const d = apenasDigitos(valor).slice(0, 11);
    let saida = d.slice(0, 3);
    if (d.length > 3) saida += "." + d.slice(3, 6);
    if (d.length > 6) saida += "." + d.slice(6, 9);
    if (d.length > 9) saida += "-" + d.slice(9, 11);
    return saida;
  },
  cep: function (valor) {
    const d = apenasDigitos(valor).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  },
  data: function (valor) {
    const d = apenasDigitos(valor).slice(0, 8);
    let saida = d.slice(0, 2);
    if (d.length > 2) saida += "/" + d.slice(2, 4);
    if (d.length > 4) saida += "/" + d.slice(4, 8);
    return saida;
  }
};

function apenasDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function criarCampo(perfil, campo) {
  const div = document.createElement("div");
  div.className = "campo col-" + campo.largura;

  const label = document.createElement("label");
  label.htmlFor = perfil + "-" + campo.nome;
  label.textContent = campo.rotulo;
  div.appendChild(label);

  let controle;
  if (campo.opcoes) {
    controle = document.createElement("select");
    const vazio = document.createElement("option");
    vazio.value = "";
    vazio.textContent = campo.exemplo;
    vazio.disabled = true;
    vazio.selected = true;
    controle.appendChild(vazio);
    for (const texto of campo.opcoes) {
      const item = document.createElement("option");
      item.value = texto;
      item.textContent = texto;
      controle.appendChild(item);
    }
  } else {
    if (campo.tipo === "textarea") {
      controle = document.createElement("textarea");
      controle.rows = 2;
    } else {
      controle = document.createElement("input");
      controle.type = campo.tipo || "text";
    }
    controle.placeholder = campo.exemplo;
  }
  controle.id = perfil + "-" + campo.nome;
  controle.name = campo.nome;
  div.appendChild(controle);
  return div;
}

function construirFormulario(perfil) {
  const form = document.getElementById("form-" + perfil);

  const containerErros = document.createElement("div");
  containerErros.className = "erros oculto";
  containerErros.setAttribute("role", "alert");
  form.appendChild(containerErros);

  for (const bloco of BLOCOS) {
    const secao = document.createElement("section");
    secao.className = "bloco";
    const titulo = document.createElement("h2");
    titulo.textContent = bloco.titulo;
    secao.appendChild(titulo);

    const grade = document.createElement("div");
    grade.className = "grade";
    for (const campo of bloco.campos) {
      if (campo.somente && campo.somente !== perfil) continue;
      grade.appendChild(criarCampo(perfil, campo));
    }
    secao.appendChild(grade);
    form.appendChild(secao);
  }

  const acoes = document.createElement("div");
  acoes.className = "acoes";
  const botao = document.createElement("button");
  botao.type = "submit";
  botao.className = "botao-enviar";
  botao.textContent = "Enviar solicitação";
  acoes.appendChild(botao);
  form.appendChild(acoes);

  for (const bloco of BLOCOS) {
    for (const campo of bloco.campos) {
      if (!campo.formatar) continue;
      const controle = form.elements.namedItem(campo.nome);
      if (!controle) continue;
      controle.addEventListener("blur", function () {
        controle.value = FORMATADORES[campo.formatar](controle.value);
      });
    }
  }

  form.addEventListener("submit", function (evento) {
    enviar(evento, form, perfil, containerErros);
  });
}

function mostrarErros(container, mensagens) {
  const linhas = mensagens.map(function (texto) {
    const linha = document.createElement("div");
    linha.textContent = texto;
    return linha;
  });
  container.replaceChildren(...linhas);
  container.classList.remove("oculto");
}

async function enviar(evento, form, perfil, containerErros) {
  evento.preventDefault();
  const dados = { perfil: perfil };
  for (const nome of NOMES_DE_CAMPO) {
    const controle = form.elements.namedItem(nome);
    if (controle) dados[nome] = controle.value;
  }

  let resposta;
  try {
    const respostaHttp = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dados)
    });
    resposta = await respostaHttp.();
  } catch (erro) {
    mostrarErros(containerErros, ["Não foi possível enviar a solicitação."]);
    return;
  }

  if (resposta.erros && resposta.erros.length > 0) {
    mostrarErros(containerErros, resposta.erros);
    return;
  }

  document.getElementById("formulario-view").classList.add("oculto");
  document.getElementById("oficio").textContent = resposta.oficio;
  document.getElementById("confirmacao-view").classList.remove("oculto");
  window.scrollTo(0, 0);
}

function alternarAba(perfil) {
  for (const nome of ["alunos", "docentes"]) {
    const ativa = nome === perfil;
    const aba = document.getElementById("aba-" + nome);
    aba.classList.toggle("ativa", ativa);
    aba.setAttribute("aria-selected", ativa ? "true" : "false");
    document.getElementById("form-" + nome).classList.toggle("oculto", !ativa);
  }
}

construirFormulario("alunos");
construirFormulario("docentes");
document.getElementById("aba-alunos").addEventListener("click", function () { alternarAba("alunos"); });
document.getElementById("aba-docentes").addEventListener("click", function () { alternarAba("docentes"); });
