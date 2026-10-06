function limpar(v) {
  return String(v).replace(/\D+/g, "");
}

function formatarMoeda(d) {
  if (!d) return "";
  d = d.replace(/^0+(?=.)/, "");
  const cent = d.slice(-2).padStart(2, "0");
  let int = d.slice(0, -2);
  if (!int || int === "") int = "0";
  const partes = [];
  while (int.length > 3) {
    partes.unshift(int.slice(-3));
    int = int.slice(0, -3);
  }
  partes.unshift(int);
  return "R$ " + partes.join(".") + "," + cent;
}

function formatarCpf(d) {
  if (d.length !== 11) return d;
  return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
}

function formatarCep(d) {
  if (d.length !== 8) return d;
  return d.slice(0, 5) + "-" + d.slice(5);
}

function formatarData(d) {
  if (d.length !== 8) return d;
  return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
}

document.addEventListener("blur", function (e) {
  const t = e.target;
  const d = limpar(t.value);
  if (t.classList.contains("auto-valor")) t.value = formatarMoeda(d);
  if (t.classList.contains("auto-cpf")) t.value = formatarCpf(d);
  if (t.classList.contains("auto-cep")) t.value = formatarCep(d);
  if (t.classList.contains("auto-data")) t.value = formatarData(d);
}, true);

document.querySelectorAll(".aba").forEach(function (aba) {
  aba.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (a) {
      a.classList.toggle("ativa", a === aba);
      a.setAttribute("aria-selected", a === aba ? "true" : "false");
    });
    document.querySelectorAll(".painel").forEach(function (p) {
      p.hidden = p.id !== "painel-" + aba.dataset.tab;
    });
  });
});

document.querySelectorAll(".form").forEach(function (form) {
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const tipo = form.id.replace("form-", "");
    const dados = { tipo: tipo };
    new FormData(form).forEach(function (v, k) { dados[k] = v; });
    fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    }).then(function (r) { return r.json(); }).then(function (corpo) {
      const caixa = form.querySelector(".erros");
      if (corpo.erros) {
        caixa.innerHTML = corpo.erros.map(function (m) { return "<p>" + m + "</p>"; }).join("");
        return;
      }
      document.querySelector("main").innerHTML =
        "<h2>Solicitação registrada</h2><pre>" + corpo.oficio + "</pre>";
    });
  });
});
