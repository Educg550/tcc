const BLOCOS = [
  {
    titulo: "SOLICITANTE E EVENTO",
    campos: [
      { nome: "nome", label: "NOME COMPLETO - SEM ABREVIAR", ph: "Maria da Silva Santos", span: 2 },
      { nome: "n_usp", label: "N. USP", ph: "12345678", span: 1 },
      { nome: "programa", label: "PROGRAMA", ph: "Ciência da Computação", span: 1 },
      { nome: "nivel", label: "NÍVEL", tipo: "select", opcoes: ["Mestrado", "Doutorado"], ph: "Selecione o nível", span: 1, soAlunos: true },
      { nome: "tipo_auxilio", label: "TIPO DE AUXÍLIO", tipo: "select", opcoes: ["Participação em evento", "Banca de exame ou defesa", "Outro"], ph: "Selecione o tipo", span: 1, soAlunos: true },
      { nome: "email", label: "E-MAIL", ph: "maria.silva@usp.br", tipo: "email", span: 2 },
      { nome: "evento", label: "NOME DO EVENTO / BANCA DE EXAME OU DEFESA", ph: "Congresso Brasileiro de Computação", span: 2 },
      { nome: "periodo", label: "PERÍODO DO EVENTO, EXAME OU DEFESA", ph: "10 a 15 de junho de 2024", span: 2 },
      { nome: "cidade_evento", label: "CIDADE DO EVENTO, EXAME OU DEFESA", ph: "São Paulo", span: 1 },
      { nome: "estado_evento", label: "ESTADO DO EVENTO, EXAME OU DEFESA", ph: "SP", span: 1 },
      { nome: "pais_evento", label: "PAÍS DO EVENTO, EXAME OU DEFESA", ph: "Brasil", span: 1 },
      { nome: "link_evento", label: "LINK DO EVENTO, EXAME OU DEFESA", ph: "https://evento.exemplo.br", span: 1, opcional: true },
      { nome: "valor", label: "VALOR SOLICITADO (R$)", ph: "150000", span: 1, formato: "moeda" },
      { nome: "detalhamento", label: "DETALHAMENTO DO PEDIDO", ph: "Descreva a finalidade do auxílio solicitado", tipo: "textarea", span: 3 },
      { nome: "apresentacao", label: "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", tipo: "select", opcoes: ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"], ph: "Selecione a apresentação", span: 1 }
    ]
  },
  {
    titulo: "ENDEREÇO DO SOLICITANTE",
    campos: [
      { nome: "data_nascimento", label: "DATA DE NASCIMENTO", ph: "01021980", span: 1, formato: "data" },
      { nome: "logradouro", label: "LOGRADOURO", ph: "Rua do Matão", span: 2 },
      { nome: "numero", label: "NÚMERO", ph: "1010", span: 1 },
      { nome: "complemento", label: "COMPLEMENTO", ph: "Sala 101", span: 1, opcional: true },
      { nome: "bairro", label: "BAIRRO", ph: "Butantã", span: 1 },
      { nome: "cep", label: "CEP", ph: "05508090", span: 1, formato: "cep" },
      { nome: "cidade", label: "CIDADE", ph: "São Paulo", span: 1 },
      { nome: "estado", label: "ESTADO", ph: "SP", span: 1 }
    ]
  },
  {
    titulo: "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    campos: [
      { nome: "cpf", label: "CPF (SEPARADOS POR PONTOS E TRAÇO)", ph: "12345678909", span: 1, formato: "cpf" },
      { nome: "rg", label: "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", ph: "12.345.678-9", span: 1 },
      { nome: "banco", label: "NOME DO BANCO", ph: "Banco do Brasil", span: 1 },
      { nome: "agencia", label: "NÚMERO DA AGÊNCIA", ph: "1234", span: 1 },
      { nome: "conta", label: "NÚMERO DA CONTA", ph: "12345-6", span: 1 }
    ]
  }
];

function formatarMoeda(v) {
  let d = v.replace(/\D/g, "");
  if (!d) return "";
  d = d.padStart(3, "0");
  const centavos = d.slice(-2);
  const inteiro = d.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + inteiro + "," + centavos;
}

function formatarCPF(v) {
  const d = v.replace(/\D/g, "").slice(0, 11);
  if (!d) return "";
  if (d.length > 9) return d.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, "$1.$2.$3-$4");
  if (d.length > 6) return d.replace(/(\d{3})(\d{3})(\d{1,3})/, "$1.$2.$3");
  if (d.length > 3) return d.replace(/(\d{3})(\d{1,3})/, "$1.$2");
  return d;
}

function formatarCEP(v) {
  const d = v.replace(/\D/g, "").slice(0, 8);
  if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
  return d;
}

function formatarData(v) {
  const d = v.replace(/\D/g, "").slice(0, 8);
  let r = d.slice(0, 2);
  if (d.length > 2) r += "/" + d.slice(2, 4);
  if (d.length > 4) r += "/" + d.slice(4, 8);
  return r;
}

function aplicarFormato(tipo, valor) {
  if (tipo === "moeda") return formatarMoeda(valor);
  if (tipo === "cpf") return formatarCPF(valor);
  if (tipo === "cep") return formatarCEP(valor);
  if (tipo === "data") return formatarData(valor);
  return valor;
}

function criarCampo(aba, c) {
  const id = aba + "-" + c.nome;
  const wrap = document.createElement("div");
  wrap.className = "campo";
  wrap.style.gridColumn = "span " + (c.span || 1);

  const label = document.createElement("label");
  label.textContent = c.label;
  label.htmlFor = id;
  wrap.appendChild(label);

  let input;
  if (c.tipo === "select") {
    input = document.createElement("select");
    const vazio = document.createElement("option");
    vazio.value = "";
    vazio.textContent = c.ph;
    input.appendChild(vazio);
    c.opcoes.forEach(function (o) {
      const opt = document.createElement("option");
      opt.value = o;
      opt.textContent = o;
      input.appendChild(opt);
    });
  } else if (c.tipo === "textarea") {
    input = document.createElement("textarea");
    input.rows = 2;
    input.placeholder = c.ph;
  } else {
    input = document.createElement("input");
    input.type = c.tipo || "text";
    input.placeholder = c.ph;
  }

  input.id = id;
  input.name = c.nome;

  if (c.formato) {
    input.addEventListener("blur", function () {
      input.value = aplicarFormato(c.formato, input.value);
    });
  }

  wrap.appendChild(input);
  return wrap;
}

function construirFormulario(aba) {
  const form = document.createElement("form");
  form.className = "formulario";
  form.dataset.aba = aba;
  form.noValidate = true;
  if (aba !== "alunos") form.classList.add("escondido");

  const erros = document.createElement("div");
  erros.className = "erros escondido";
  form.appendChild(erros);

  BLOCOS.forEach(function (bloco) {
    const sec = document.createElement("section");
    sec.className = "bloco";
    const titulo = document.createElement("h2");
    titulo.textContent = bloco.titulo;
    sec.appendChild(titulo);

    const grid = document.createElement("div");
    grid.className = "grid";
    bloco.campos.forEach(function (c) {
      if (c.soAlunos && aba !== "alunos") return;
      grid.appendChild(criarCampo(aba, c));
    });
    sec.appendChild(grid);
    form.appendChild(sec);
  });

  const botao = document.createElement("button");
  botao.type = "submit";
  botao.className = "enviar";
  botao.textContent = "Enviar solicitação";
  form.appendChild(botao);

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    enviar(form);
  });

  return form;
}

async function enviar(form) {
  const dados = { aba: form.dataset.aba };
  form.querySelectorAll("input, select, textarea").forEach(function (el) {
    dados[el.name] = el.value;
  });

  const resposta = await fetch("/api/solicitar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados)
  });
  const json = await resposta.json();

  const caixa = form.querySelector(".erros");
  if (json.erros && json.erros.length > 0) {
    caixa.innerHTML = "";
    json.erros.forEach(function (msg) {
      const linha = document.createElement("div");
      linha.textContent = msg;
      caixa.appendChild(linha);
    });
    caixa.classList.remove("escondido");
    return;
  }

  caixa.classList.add("escondido");
  document.getElementById("oficio").textContent = json.oficio;
  document.getElementById("formularios").classList.add("escondido");
  document.getElementById("abas").classList.add("escondido");
  document.getElementById("confirmacao").classList.remove("escondido");
}

document.getElementById("formularios").appendChild(construirFormulario("alunos"));
document.getElementById("formularios").appendChild(construirFormulario("docentes"));

document.querySelectorAll(".aba").forEach(function (botao) {
  botao.addEventListener("click", function () {
    const aba = botao.dataset.aba;
    document.querySelectorAll(".aba").forEach(function (b) {
      b.classList.toggle("ativa", b === botao);
    });
    document.querySelectorAll(".formulario").forEach(function (f) {
      f.classList.toggle("escondido", f.dataset.aba !== aba);
    });
  });
});
