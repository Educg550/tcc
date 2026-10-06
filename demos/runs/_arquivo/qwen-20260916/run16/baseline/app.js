"use strict";

var CAMPOS = [
  ["bloco", "SOLICITANTE E EVENTO"],
  ["text", "nome", "NOME COMPLETO - SEM ABREVIAR", "José da Silva Santos"],
  ["text", "n_usp", "N. USP", "12345678"],
  ["text", "programa", "PROGRAMA", "Matemática"],
  ["select", "nivel", "NÍVEL", ["Mestrado", "Doutorado"]],
  ["select", "tipo_auxilio", "TIPO DE AUXÍLIO", ["Participação em evento", "Banca de exame ou defesa", "Outro"]],
  ["email", "email", "E-MAIL", "nome@exemplo.com"],
  ["text", "nome_evento", "NOME DO EVENTO / BANCA DE EXAME OU DEFESA", "XXVIII Colóquio Brasileiro de Matemática"],
  ["text", "periodo", "PERÍODO DO EVENTO, EXAME OU DEFESA", "10/07/2025 a 18/07/2025"],
  ["text", "cidade_evento", "CIDADE DO EVENTO, EXAME OU DEFESA", "São Carlos"],
  ["text", "estado_evento", "ESTADO DO EVENTO, EXAME OU DEFESA", "SP"],
  ["text", "pais_evento", "PAÍS DO EVENTO, EXAME OU DEFESA", "Brasil"],
  ["text", "link", "LINK DO EVENTO, EXAME OU DEFESA", "https://exemplo.com/evento", "opcional"],
  ["valor", "valor", "VALOR SOLICITADO (R$)", "R$ 1.500,00"],
  ["textarea", "detalhamento", "DETALHAMENTO DO PEDIDO", "Solicito auxílio para custear transporte e hospedagem durante o evento."],
  ["select", "apresentacao", "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"]],
  ["bloco", "ENDEREÇO DO SOLICITANTE"],
  ["data", "data_nascimento", "DATA DE NASCIMENTO", "01/02/1980"],
  ["text", "logradouro", "LOGRADOURO", "Rua do Matão"],
  ["text", "numero", "NÚMERO", "1010"],
  ["text", "complemento", "COMPLEMENTO", "Apto 32", "opcional"],
  ["text", "bairro", "BAIRRO", "Butantã"],
  ["cep", "cep", "CEP", "05508-090"],
  ["text", "cidade", "CIDADE", "São Paulo"],
  ["text", "estado", "ESTADO", "SP"],
  ["bloco", "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO"],
  ["cpf", "cpf", "CPF (SEPARADOS POR PONTOS E TRAÇO)", "123.456.789-09"],
  ["text", "rg", "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", "12.345.678-9"],
  ["text", "banco", "NOME DO BANCO", "Banco do Brasil S.A."],
  ["text", "agencia", "NÚMERO DA AGÊNCIA", "1234"],
  ["text", "conta", "NÚMERO DA CONTA", "123456-7"]
];

function soDigitos(texto) {
  return texto.replace(/\D+/g, "");
}

function formatarMoeda(centavos) {
  var inteiro = Math.floor(centavos / 100);
  var resto = String(centavos % 100);
  if (resto.length < 2) resto = "0" + resto;
  var comMilhar = String(inteiro).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + comMilhar + "," + resto;
}

function formatarCPF(digitos) {
  var d = digitos.slice(0, 11);
  var s = d.slice(0, 3);
  if (d.length > 3) s += "." + d.slice(3, 6);
  if (d.length > 6) s += "." + d.slice(6, 9);
  if (d.length > 9) s += "-" + d.slice(9);
  return s;
}

function formatarCEP(digitos) {
  var d = digitos.slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(digitos) {
  var d = digitos.slice(0, 8);
  var s = d.slice(0, 2);
  if (d.length > 2) s += "/" + d.slice(2, 4);
  if (d.length > 4) s += "/" + d.slice(4);
  return s;
}

function rotuloDo(especie, rotulo) {
  return especie === "valor" ? rotulo : rotulo;
}

function construirFormulario(form, tipo) {
  CAMPOS.forEach(function (c) {
    if (c[0] === "bloco") {
      var bloco = document.createElement("div");
      bloco.className = "bloco";
      var titulo = document.createElement("h3");
      titulo.textContent = c[1];
      bloco.appendChild(titulo);
      bloco.appendChild(document.createElement("div")).className = "grade";
      form._grade = bloco.lastChild;
      form.appendChild(bloco);
      return;
    }
    var especie = c[0], nome = c[1], rotulo = c[2], placeholder = c[3];
    if (tipo === "docentes" && (nome === "nivel" || nome === "tipo_auxilio")) return;

    var campo = document.createElement("div");
    campo.className = "campo";
    campo.id = "f-" + nome;

    var label = document.createElement("label");
    label.textContent = rotulo;
    label.setAttribute("for", tipo + "-" + nome);

    var controle;
    if (especie === "select") {
      controle = document.createElement("select");
      var vazio = document.createElement("option");
      vazio.value = "";
      vazio.textContent = placeholder || "Selecione";
      controle.appendChild(vazio);
      c[3].forEach(function (opcao) {
        var o = document.createElement("option");
        o.value = opcao;
        o.textContent = opcao;
        controle.appendChild(o);
      });
    } else {
      controle = document.createElement(especie === "textarea" ? "textarea" : "input");
      if (especie !== "textarea") {
        controle.type = (especie === "email") ? "email" : "text";
        controle.autocomplete = "off";
      }
      controle.placeholder = placeholder || "";
      if (especie === "valor") controle.addEventListener("input", function () { this.value = soDigitos(this.value); });
      if (especie === "cep" || especie === "cpf" || especie === "data") {
        controle.addEventListener("input", function () { this.value = soDigitos(this.value); });
      }
      controle.addEventListener("blur", function () {
        var d = soDigitos(this.value);
        if (especie === "valor") this.value = d ? formatarMoeda(parseInt(d, 10)) : "";
        if (especie === "cpf") this.value = formatarCPF(d);
        if (especie === "cep") this.value = formatarCEP(d);
        if (especie === "data") this.value = formatarData(d);
      });
    }
    controle.id = tipo + "-" + nome;
    controle.name = nome;

    campo.appendChild(label);
    campo.appendChild(controle);
    form._grade.appendChild(campo);
  });

  var botao = document.createElement("button");
  botao.type = "submit";
  botao.className = "enviar";
  botao.textContent = "Enviar solicitação";
  form.appendChild(botao);
}

function coletar(form, tipo) {
  var dados = { tipo: tipo };
  CAMPOS.forEach(function (c) {
    if (c[0] === "bloco") return;
    var nome = c[1];
    if (tipo === "docentes" && (nome === "nivel" || nome === "tipo_auxilio")) return;
    var el = form.elements[nome];
    var valor = el.value.trim();
    if (nome === "valor" || nome === "cep" || nome === "cpf" || nome === "data_nascimento") {
      valor = (nome === "cep") ? formatarCEP(soDigitos(valor))
            : (nome === "cpf") ? formatarCPF(soDigitos(valor))
            : (nome === "data_nascimento") ? formatarData(soDigitos(valor))
            : (soDigitos(valor) ? parseInt(soDigitos(valor), 10) : valor);
    }
    dados[nome] = valor;
  });
  return dados;
}

function mostrarErros(lista) {
  var caixa = document.getElementById("erros");
  caixa.textContent = lista.join("\n");
  caixa.hidden = lista.length === 0;
}

function enviar(evento) {
  evento.preventDefault();
  var form = evento.target;
  var tipo = form.id.replace("form-", "");
  fetch("/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(coletar(form, tipo))
  })
    .then(function (r) { return r.json(); })
    .then(function (resposta) {
      if (resposta.erros) {
        mostrarErros(resposta.erros);
        return;
      }
      document.getElementById("painel").hidden = true;
      document.getElementById("oficio").textContent = resposta.oficio;
      document.getElementById("confirmacao").hidden = false;
    })
    .catch(function () { mostrarErros(["Falha ao comunicar com o servidor"]); });
}

construirFormulario(document.getElementById("form-alunos"), "alunos");
construirFormulario(document.getElementById("form-docentes"), "docentes");

var abaAlunos = document.getElementById("aba-alunos");
var abaDocentes = document.getElementById("aba-docentes");
var formAlunos = document.getElementById("form-alunos");
var formDocentes = document.getElementById("form-docentes");

function trocarPara(alunos) {
  abaAlunos.classList.toggle("ativa", alunos);
  abaDocentes.classList.toggle("ativa", !alunos);
  abaAlunos.setAttribute("aria-selected", String(alunos));
  abaDocentes.setAttribute("aria-selected", String(!alunos));
  formAlunos.hidden = !alunos;
  formDocentes.hidden = alunos;
  mostrarErros([]);
}

abaAlunos.addEventListener("click", function () { trocarPara(true); });
abaDocentes.addEventListener("click", function () { trocarPara(false); });

formAlunos.addEventListener("submit", enviar);
formDocentes.addEventListener("submit", enviar);
