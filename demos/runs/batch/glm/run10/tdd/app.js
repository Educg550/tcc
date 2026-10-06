function formatarMoeda(valor) {
  var d = (valor || "").replace(/\D/g, "");
  if (!d) return "";
  var cent = d.slice(-2).padStart(2, "0");
  var inteiro = d.slice(0, -2) || "0";
  var grupos = [];
  while (inteiro.length > 3) {
    grupos.unshift(inteiro.slice(-3));
    inteiro = inteiro.slice(0, -3);
  }
  grupos.unshift(inteiro);
  return "R$ " + grupos.join(".") + "," + cent;
}

function formatarCPF(valor) {
  var d = valor.replace(/\D/g, "").slice(0, 11);
  if (d.length !== 11) return d;
  return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
}

function formatarCEP(valor) {
  var d = valor.replace(/\D/g, "").slice(0, 8);
  if (d.length !== 8) return d;
  return d.slice(0, 5) + "-" + d.slice(5);
}

function formatarData(valor) {
  var d = valor.replace(/\D/g, "").slice(0, 8);
  if (d.length !== 8) return d;
  return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
}

function amarrarFormato(classe, funcao) {
  document.querySelectorAll("." + classe).forEach(function (el) {
    el.addEventListener("blur", function () {
      el.value = funcao(el.value);
    });
  });
}

amarrarFormato("campo-moeda", formatarMoeda);
amarrarFormato("campo-cpf", formatarCPF);
amarrarFormato("campo-cep", formatarCEP);
amarrarFormato("campo-data", formatarData);

function ativarAba(nome) {
  document.querySelectorAll(".aba").forEach(function (botao) {
    botao.classList.toggle("ativa", botao.dataset.aba === nome);
  });
  document.querySelectorAll(".painel").forEach(function (painel) {
    painel.classList.toggle("oculto", painel.dataset.aba !== nome);
  });
}

document.querySelectorAll(".aba").forEach(function (botao) {
  botao.addEventListener("click", function () {
    ativarAba(botao.dataset.aba);
  });
});

function configurarForm(formId, aba) {
  var form = document.getElementById(formId);
  form.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    var dados = Object.fromEntries(new FormData(form).entries());
    dados.aba = aba;
    var resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    var corpo = await resposta.json();
    var erros = document.getElementById("erros-" + aba);
    if (!resposta.ok) {
      erros.replaceChildren(
        ...corpo.errors.map(function (mensagem) {
          var div = document.createElement("div");
          div.textContent = mensagem;
          return div;
        })
      );
    } else {
      erros.replaceChildren();
      document.getElementById("oficio").textContent = corpo.oficio;
      document.getElementById("formulario").classList.add("oculto");
      document.querySelector(".abas").classList.add("oculto");
      document.getElementById("confirmacao").classList.remove("oculto");
    }
  });
}

configurarForm("form-alunos", "alunos");
configurarForm("form-docentes", "docentes");
