function formatarMoeda(valor) {
  const d = (valor || "").replace(/\D/g, "");
  if (!d) return "";
  const n = parseInt(d, 10) / 100;
  return "R$ " + n.toLocaleString("pt-BR", { minimumFractionDigits: 2 });
}

function formatarCpf(valor) {
  const d = (valor || "").replace(/\D/g, "").slice(0, 11);
  if (d.length !== 11) return valor;
  return d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
}

function formatarCep(valor) {
  const d = (valor || "").replace(/\D/g, "").slice(0, 8);
  if (d.length !== 8) return valor;
  return d.replace(/(\d{5})(\d{3})/, "$1-$2");
}

function formatarData(valor) {
  const d = (valor || "").replace(/\D/g, "").slice(0, 8);
  if (d.length !== 8) return valor;
  return d.replace(/(\d{2})(\d{2})(\d{4})/, "$1/$2/$3");
}

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".moeda").forEach(function (el) {
    el.addEventListener("blur", function () { el.value = formatarMoeda(el.value); });
    el.addEventListener("focus", function () { el.value = el.value.replace(/\D/g, ""); });
  });
  document.querySelectorAll(".cpf").forEach(function (el) {
    el.addEventListener("blur", function () { el.value = formatarCpf(el.value); });
  });
  document.querySelectorAll(".cep").forEach(function (el) {
    el.addEventListener("blur", function () { el.value = formatarCep(el.value); });
  });
  document.querySelectorAll(".data").forEach(function (el) {
    el.addEventListener("blur", function () { el.value = formatarData(el.value); });
  });

  document.querySelectorAll(".aba").forEach(function (botao) {
    botao.addEventListener("click", function () {
      document.querySelectorAll(".aba").forEach(function (b) { b.classList.remove("ativa"); });
      botao.classList.add("ativa");
      document.querySelectorAll(".painel").forEach(function (p) { p.classList.add("oculto"); });
      document.getElementById("painel-" + botao.dataset.aba).classList.remove("oculto");
    });
  });

  ["ALUNOS", "DOCENTES"].forEach(function (aba) {
    document.getElementById("form-" + aba).addEventListener("submit", function (e) {
      e.preventDefault();
      const dados = {};
      new FormData(e.target).forEach(function (v, k) { dados[k] = v; });
      dados["aba"] = aba;
      fetch("/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (r) { return r.json(); })
        .then(function (res) {
          const el = document.getElementById("erros-" + aba);
          if (res.ok) {
            document.querySelector("main").classList.add("oculto");
            const confirmacao = document.getElementById("confirmacao");
            confirmacao.classList.remove("oculto");
            document.getElementById("oficio").textContent = res.oficio;
          } else {
            el.innerHTML = "";
            (res.erros || []).forEach(function (msg) {
              const p = document.createElement("p");
              p.textContent = msg;
              el.appendChild(p);
            });
          }
        });
    });
  });
});
