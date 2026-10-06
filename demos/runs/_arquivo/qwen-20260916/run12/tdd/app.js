(function () {
  "use strict";

  var APRESENTACOES = [
    "Poster",
    "Apresentacao oral",
    "Outra",
    "Nao ira apresentar trabalho"
  ];

  var BLOCOS = [
    {
      titulo: "SOLICITANTE E EVENTO",
      campos: [
        { id: "nome", rotulo: "NOME COMPLETO - SEM ABREVIAR", placeholder: "Maria da Silva", classe: "medio" },
        { id: "nusp", rotulo: "N. USP", placeholder: "123456", classe: "" },
        { id: "programa", rotulo: "PROGRAMA", placeholder: "Matemática", classe: "" },
        { id: "nivel", rotulo: "NÍVEL", somente: "alunos", tipo: "select", opcoes: ["", "Mestrado", "Doutorado"] },
        { id: "tipoAuxilio", rotulo: "TIPO DE AUXÍLIO", somente: "alunos", tipo: "select", opcoes: ["", "Participação em evento", "Banca de exame ou defesa", "Outro"] },
        { id: "email", rotulo: "E-MAIL", placeholder: "nome@ime.usp.br", classe: "medio" },
        { id: "nomeEvento", rotulo: "NOME DO EVENTO / BANCA DE EXAME OU DEFESA", placeholder: "Congresso de Matemática", classe: "medio" },
        { id: "periodoEvento", rotulo: "PERÍODO DO EVENTO, EXAME OU DEFESA", placeholder: "10 a 14 de novembro de 2025", classe: "" },
        { id: "cidadeEvento", rotulo: "CIDADE DO EVENTO, EXAME OU DEFESA", placeholder: "São Paulo", classe: "" },
        { id: "estadoEvento", rotulo: "ESTADO DO EVENTO, EXAME OU DEFESA", placeholder: "SP", classe: "" },
        { id: "paisEvento", rotulo: "PAÍS DO EVENTO, EXAME OU DEFESA", placeholder: "Brasil", classe: "" },
        { id: "linkEvento", rotulo: "LINK DO EVENTO, EXAME OU DEFESA", placeholder: "https://exemplo.org/evento", opcional: true, classe: "medio" },
        { id: "valor", rotulo: "VALOR SOLICITADO (R$)", placeholder: "R$ 1.500,00", mascara: "valor", classe: "" },
        { id: "apresentacao", rotulo: "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", tipo: "select", opcoes: APRESENTACOES.slice(), classe: "medio" },
        { id: "detalhamento", rotulo: "DETALHAMENTO DO PEDIDO", placeholder: "Participação em congresso na área de análise", tipo: "textarea", classe: "longo" }
      ]
    },
    {
      titulo: "ENDEREÇO DO SOLICITANTE",
      campos: [
        { id: "dataNascimento", rotulo: "DATA DE NASCIMENTO", placeholder: "01/02/1980", mascara: "data", classe: "" },
        { id: "cep", rotulo: "CEP", placeholder: "05508-090", mascara: "cep", classe: "" },
        { id: "logradouro", rotulo: "LOGRADOURO", placeholder: "Rua do Matão", classe: "medio" },
        { id: "numero", rotulo: "NÚMERO", placeholder: "1010", classe: "" },
        { id: "complemento", rotulo: "COMPLEMENTO", placeholder: "Apto 42", opcional: true, classe: "medio" },
        { id: "bairro", rotulo: "BAIRRO", placeholder: "Butantã", classe: "" },
        { id: "cidade", rotulo: "CIDADE", placeholder: "São Paulo", classe: "" },
        { id: "estado", rotulo: "ESTADO", placeholder: "SP", classe: "" }
      ]
    },
    {
      titulo: "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
      campos: [
        { id: "cpf", rotulo: "CPF (SEPARADOS POR PONTOS E TRAÇO)", placeholder: "123.456.789-09", mascara: "cpf", classe: "" },
        { id: "rg", rotulo: "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", placeholder: "12.345.678-9", classe: "" },
        { id: "banco", rotulo: "NOME DO BANCO", placeholder: "Banco do Brasil", classe: "" },
        { id: "agencia", rotulo: "NÚMERO DA AGÊNCIA", placeholder: "1234", classe: "" },
        { id: "conta", rotulo: "NÚMERO DA CONTA", placeholder: "12345678-9", classe: "" }
      ]
    }
  ];

  function formatador(valor, tipo) {
    var digitos = valor.replace(/\D/g, "");
    if (tipo === "valor") {
      var inteiro = parseInt(digitos, 10) || 0;
      var centavos = String(inteiro % 100).padStart(2, "0");
      var texto = String(Math.floor(inteiro / 100));
      var formatado = "";
      while (texto.length > 3) {
        formatado = "." + texto.slice(-3) + formatado;
        texto = texto.slice(0, -3);
      }
      return "R$ " + texto + formatado + "," + centavos;
    }
    if (tipo === "cpf") {
      digitos = digitos.slice(0, 11);
      return digitos
        .replace(/(\d{3})(\d{0,3})/, "$1.$2")
        .replace(/(\d{3})\.(\d{3})(\d{0,3})/, "$1.$2.$3")
        .replace(/(\d{3})\.(\d{3})\.(\d{3})(\d{0,2})/, "$1.$2.$3-$4");
    }
    if (tipo === "cep") {
      digitos = digitos.slice(0, 8);
      return digitos.replace(/(\d{5})(\d{3})/, "$1-$2");
    }
    if (tipo === "data") {
      digitos = digitos.slice(0, 8);
      return digitos.replace(/(\d{2})(\d{2})(\d{4})/, "$1/$2/$3")
        .replace(/(\d{2})(\d{0,2})/, "$1/$2");
    }
    return valor;
  }

  function soDigitos(input) {
    input.addEventListener("input", function () {
      input.value = input.value.replace(/\D/g, "");
    });
  }

  function montaFormulario(form, aba) {
    form.setAttribute("data-aba", aba);
    BLOCOS.forEach(function (bloco) {
      var secao = document.createElement("section");
      secao.className = "bloco";
      var h = document.createElement("h3");
      h.textContent = bloco.titulo;
      secao.appendChild(h);
      var grade = document.createElement("div");
      grade.className = "campos";
      bloco.campos.forEach(function (campo) {
        if (campo.somente && campo.somente !== aba) return;
        var wrapper = document.createElement("div");
        wrapper.className = "campo" + (campo.classe ? " " + campo.classe : "");
        var label = document.createElement("label");
        var id = aba + "-" + campo.id;
        label.setAttribute("for", id);
        label.textContent = campo.rotulo;
        wrapper.appendChild(label);
        var el;
        if (campo.tipo === "select") {
          el = document.createElement("select");
          campo.opcoes.forEach(function (opcao, indice) {
            var o = document.createElement("option");
            o.value = opcao;
            o.textContent = opcao || "-";
            if (indice === 0) o.disabled = true;
            el.appendChild(o);
          });
        } else if (campo.tipo === "textarea") {
          el = document.createElement("textarea");
          el.rows = 2;
        } else {
          el = document.createElement("input");
          el.type = "text";
          if (campo.id === "nusp" || campo.id === "agencia") soDigitos(el);
        }
        if (campo.placeholder) el.placeholder = campo.placeholder;
        if (campo.opcional) { el.dataset.opcional = "1"; }
        el.id = id;
        el.name = campo.id;
        if (campo.mascara) {
          el.dataset.mascara = campo.mascara;
          el.addEventListener("blur", function () {
            el.value = formatador(el.value, campo.mascara);
          });
        }
        wrapper.appendChild(el);
        grade.appendChild(wrapper);
      });
      secao.appendChild(grade);
      form.appendChild(secao);
    });

    var botao = document.createElement("button");
    botao.type = "submit";
    botao.className = "enviar";
    botao.textContent = "Enviar solicitação";
    form.appendChild(botao);
  }

  function coletar(form) {
    var dados = { tipo: form.getAttribute("data-aba") };
    form.querySelectorAll("input, select, textarea").forEach(function (el) {
      var valor = el.value;
      if (el.name === "valor") valor = valor.replace(/\D/g, "");
      dados[el.name] = valor;
    });
    return dados;
  }

  function envia(e) {
    e.preventDefault();
    var form = e.currentTarget;
    var aba = form.getAttribute("data-aba");
    var caixa = document.getElementById("erros-" + aba);
    caixa.textContent = "";
    fetch("/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(coletar(form))
    })
      .then(function (r) { return r.json(); })
      .then(function (resposta) {
        if (resposta.errors && resposta.errors.length) {
          caixa.textContent = resposta.errors.join("\n");
          return;
        }
        document.getElementById("oficio").textContent = resposta.oficio;
        document.getElementById("painel-alunos").classList.remove("ativo");
        document.getElementById("painel-docentes").classList.remove("ativo");
        document.getElementById("confirmacao").classList.add("ativo");
      });
  }

  function ligaAbas() {
    document.querySelectorAll(".tab").forEach(function (botao) {
      botao.addEventListener("click", function () {
        document.querySelectorAll(".tab").forEach(function (b) { b.classList.remove("active"); });
        botao.classList.add("active");
        document.getElementById("confirmacao").classList.remove("ativo");
        ["alunos", "docentes"].forEach(function (nome) {
          document.getElementById("painel-" + nome).classList.toggle("ativo", nome === botao.dataset.alvo);
        });
      });
    });
  }

  montaFormulario(document.getElementById("form-alunos"), "alunos");
  montaFormulario(document.getElementById("form-docentes"), "docentes");
  document.getElementById("form-alunos").addEventListener("submit", envia);
  document.getElementById("form-docentes").addEventListener("submit", envia);
  ligaAbas();
})();
