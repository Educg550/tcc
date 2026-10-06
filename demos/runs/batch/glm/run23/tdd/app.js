// Comportamento de tela da solicitação de auxílio financeiro.

document.querySelectorAll(".aba").forEach(function (aba) {
  aba.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (b) { b.classList.remove("ativa"); });
    aba.classList.add("ativa");
    document.querySelectorAll(".painel").forEach(function (p) { p.classList.remove("ativo"); });
    document.getElementById("painel-" + aba.dataset.aba).classList.add("ativo");
  });
});

// Formatação automática: o backend formata, o frontend mostra.
document.querySelectorAll("[data-formata]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    fetch("/api/formata", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ campo: campo.dataset.formata, valor: campo.value })
    })
      .then(function (r) { return r.json(); })
      .then(function (dados) { campo.value = dados.formatado; });
  });
});

function coletar(form) {
  var dados = { tipo: form.id === "form-alunos" ? "alunos" : "docentes" };
  new FormData(form).forEach(function (valor, nome) { dados[nome] = valor; });
  return dados;
}

function mostrarErros(id, erros) {
  var caixa = document.getElementById(id);
  caixa.innerHTML = "";
  erros.forEach(function (msg) {
    var p = document.createElement("p");
    p.textContent = msg;
    caixa.appendChild(p);
  });
}

document.querySelectorAll("form").forEach(function (form) {
  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    var aba = form.id === "form-alunos" ? "alunos" : "docentes";
    fetch("/api/validar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(coletar(form))
    })
      .then(function (r) { return r.json(); })
      .then(function (dados) {
        if (dados.erros.length) {
          mostrarErros("erros-" + aba, dados.erros);
          return;
        }
        document.getElementById("pagina-form").hidden = true;
        document.getElementById("oficio").textContent = dados.oficio;
        document.getElementById("pagina-conf").hidden = false;
      });
  });
});

document.getElementById("voltar").addEventListener("click", function () {
  document.getElementById("pagina-conf").hidden = true;
  document.getElementById("pagina-form").hidden = false;
});
