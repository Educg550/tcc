const CAMPOS_SOLICITANTE = [
  { id: "nome", label: "NOME COMPLETO - SEM ABREVIAR", ph: "Maria da Silva Santos" },
  { id: "n_usp", label: "N. USP", ph: "12345678" },
  { id: "programa", label: "PROGRAMA", ph: "Ciência da Computação" },
  { id: "nivel", label: "NÍVEL", tipo: "select", opcoes: ["Mestrado", "Doutorado"], apenasAlunos: true },
  { id: "tipo_auxilio", label: "TIPO DE AUXÍLIO", tipo: "select", opcoes: ["Participação em evento", "Banca de exame ou defesa", "Outro"], apenasAlunos: true },
  { id: "email", label: "E-MAIL", ph: "maria.santos@usp.br" },
  { id: "evento", label: "NOME DO EVENTO / BANCA DE EXAME OU DEFESA", ph: "Congresso Brasileiro de Computação" },
  { id: "periodo", label: "PERÍODO DO EVENTO, EXAME OU DEFESA", ph: "10 a 15 de julho de 2026" },
  { id: "cidade_evento", label: "CIDADE DO EVENTO, EXAME OU DEFESA", ph: "São Paulo" },
  { id: "estado_evento", label: "ESTADO DO EVENTO, EXAME OU DEFESA", ph: "SP" },
  { id: "pais_evento", label: "PAÍS DO EVENTO, EXAME OU DEFESA", ph: "Brasil" },
  { id: "link", label: "LINK DO EVENTO, EXAME OU DEFESA", ph: "https://evento.exemplo.br", opcional: true },
  { id: "valor", label: "VALOR SOLICITADO (R$)", ph: "R$ 1.500,00", fmt: "money" },
  { id: "detalhamento", label: "DETALHAMENTO DO PEDIDO", ph: "Passagens aéreas e hospedagem", tipo: "textarea" },
  { id: "apresentacao", label: "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", tipo: "select", opcoes: ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"] }
];

const CAMPOS_ENDERECO = [
  { id: "data_nascimento", label: "DATA DE NASCIMENTO", ph: "01/02/1980", fmt: "date" },
  { id: "logradouro", label: "LOGRADOURO", ph: "Av. Prof. Luciano Gualberto" },
  { id: "numero", label: "NÚMERO", ph: "158" },
  { id: "complemento", label: "COMPLEMENTO", ph: "Bloco A, sala 100", opcional: true },
  { id: "bairro", label: "BAIRRO", ph: "Butantã" },
  { id: "cep", label: "CEP", ph: "05508-090", fmt: "cep" },
  { id: "cidade", label: "CIDADE", ph: "São Paulo" },
  { id: "estado", label: "ESTADO", ph: "SP" }
];

const CAMPOS_PAGAMENTO = [
  { id: "cpf", label: "CPF (SEPARADOS POR PONTOS E TRAÇO)", ph: "123.456.789-09", fmt: "cpf" },
  { id: "rg", label: "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", ph: "12.345.678-9" },
  { id: "banco", label: "NOME DO BANCO", ph: "Banco do Brasil" },
  { id: "agencia", label: "NÚMERO DA AGÊNCIA", ph: "12345" },
  { id: "conta", label: "NÚMERO DA CONTA", ph: "12345-6" }
];

function soDigitos(valor) {
  return valor.replace(/\D/g, "");
}

function formatarMoeda(valor) {
  const digitos = soDigitos(valor);
  if (!digitos) return "";
  const n = digitos.padStart(3, "0");
  const centavos = n.slice(-2);
  let inteiro = n.slice(0, -2).replace(/^0+(?=\d)/, "");
  inteiro = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + inteiro + "," + centavos;
}

function formatarCpf(valor) {
  const d = soDigitos(valor).slice(0, 11);
  if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
  return d;
}

function formatarCep(valor) {
  const d = soDigitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(valor) {
  const d = soDigitos(valor).slice(0, 8);
  if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
  return d;
}

function formatar(tipo, valor) {
  if (tipo === "money") return formatarMoeda(valor);
  if (tipo === "cpf") return formatarCpf(valor);
  if (tipo === "cep") return formatarCep(valor);
  if (tipo === "date") return formatarData(valor);
  return valor;
}

function criarCampo(campo) {
  const rotulo = document.createElement("label");
  rotulo.className = "campo";

  const texto = document.createElement("span");
  texto.textContent = campo.label;
  rotulo.appendChild(texto);

  let el;
  if (campo.tipo === "select") {
    el = document.createElement("select");
    const vazio = document.createElement("option");
    vazio.value = "";
    vazio.textContent = "Selecione";
    el.appendChild(vazio);
    for (const opcao of campo.opcoes) {
      const opt = document.createElement("option");
      opt.value = opcao;
      opt.textContent = opcao;
      el.appendChild(opt);
    }
  } else if (campo.tipo === "textarea") {
    el = document.createElement("textarea");
    rotulo.classList.add("longo");
  } else {
    el = document.createElement("input");
    el.type = "text";
  }

  el.name = campo.id;
  if (campo.ph) el.placeholder = campo.ph;
  if (campo.fmt) {
    el.addEventListener("blur", () => { el.value = formatar(campo.fmt, el.value); });
  }

  rotulo.appendChild(el);
  return rotulo;
}

function blocosDaAba(aba) {
  const solicitante = aba === "alunos"
    ? CAMPOS_SOLICITANTE
    : CAMPOS_SOLICITANTE.filter((c) => !c.apenasAlunos);
  return [
    { titulo: "SOLICITANTE E EVENTO", campos: solicitante },
    { titulo: "ENDEREÇO DO SOLICITANTE", campos: CAMPOS_ENDERECO },
    { titulo: "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO", campos: CAMPOS_PAGAMENTO },
  ];
}

function criarFormulario(aba) {
  const form = document.createElement("form");
  form.className = "formulario";
  form.noValidate = true;

  const erros = document.createElement("div");
  erros.className = "erros escondido";
  form.appendChild(erros);

  for (const bloco of blocosDaAba(aba)) {
    const fieldset = document.createElement("fieldset");
    fieldset.className = "bloco";
    const legend = document.createElement("legend");
    legend.textContent = bloco.titulo;
    fieldset.appendChild(legend);

    const grade = document.createElement("div");
    grade.className = "grade";
    for (const campo of bloco.campos) grade.appendChild(criarCampo(campo));
    fieldset.appendChild(grade);
    form.appendChild(fieldset);
  }

  const botao = document.createElement("button");
  botao.type = "submit";
  botao.className = "enviar";
  botao.textContent = "Enviar solicitação";
  form.appendChild(botao);

  form.addEventListener("submit", (evento) => enviar(evento, form, erros, aba));
  return form;
}

async function enviar(evento, form, erros, aba) {
  evento.preventDefault();

  const dados = { aba: aba };
  form.querySelectorAll("input, select, textarea").forEach((el) => { dados[el.name] = el.value; });

  const resposta = await fetch("/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });
  const resultado = await resposta.json();

  if (resultado.erros && resultado.erros.length) {
    erros.textContent = "";
    for (const mensagem of resultado.erros) {
      const linha = document.createElement("div");
      linha.textContent = mensagem;
      erros.appendChild(linha);
    }
    erros.classList.remove("escondido");
  } else {
    erros.classList.add("escondido");
    mostrarConfirmacao(resultado.oficio);
  }
}

function mostrarConfirmacao(oficio) {
  document.querySelector(".abas").classList.add("escondido");
  document.querySelectorAll(".painel").forEach((painel) => painel.classList.add("escondido"));

  const secao = document.getElementById("confirmacao");
  secao.textContent = "";

  const titulo = document.createElement("h2");
  titulo.textContent = "Solicitação registrada";
  secao.appendChild(titulo);

  const pre = document.createElement("pre");
  pre.className = "oficio";
  pre.textContent = oficio;
  secao.appendChild(pre);

  secao.classList.remove("escondido");
}

function ativarAba(aba) {
  const alunos = aba === "alunos";
  document.getElementById("tab-alunos").classList.toggle("ativa", alunos);
  document.getElementById("tab-docentes").classList.toggle("ativa", !alunos);
  document.getElementById("tab-alunos").setAttribute("aria-selected", String(alunos));
  document.getElementById("tab-docentes").setAttribute("aria-selected", String(!alunos));
  document.getElementById("painel-alunos").classList.toggle("escondido", !alunos);
  document.getElementById("painel-docentes").classList.toggle("escondido", alunos);
}

document.getElementById("painel-alunos").appendChild(criarFormulario("alunos"));
document.getElementById("painel-docentes").appendChild(criarFormulario("docentes"));

document.getElementById("tab-alunos").addEventListener("click", () => ativarAba("alunos"));
document.getElementById("tab-docentes").addEventListener("click", () => ativarAba("docentes"));
