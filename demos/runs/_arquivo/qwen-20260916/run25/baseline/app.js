// ---------- formatação ao sair do campo ----------
function apara(v, max) {
  var s = v.replace(/\D/g, "");
  return max ? s.slice(0, max) : s;
}

var FORMATADORES = {
  moeda: function (v) {
    var centavos = apara(v) || "0";
    var valor = (parseInt(centavos, 10) / 100).toFixed(2);
    var partes = valor.split(".");
    partes[0] = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + partes.join(",");
  },
  cpf: function (v) {
    var d = apara(v, 11), r = d.slice(0, 3);
    if (d.length > 3) r += "." + d.slice(3, 6);
    if (d.length > 6) r += "." + d.slice(6, 9);
    if (d.length > 9) r += "-" + d.slice(9, 11);
    return r;
  },
  cep: function (v) {
    var d = apara(v, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  },
  data: function (v) {
    var d = apara(v, 8), r = d.slice(0, 2);
    if (d.length > 2) r += "/" + d.slice(2, 4);
    if (d.length > 4) r += "/" + d.slice(4, 8);
    return r;
  }
};

document.addEventListener("focusout", function (ev) {
  var f = ev.target.closest ? ev.target.closest(".moeda,.cpf,.cep,.data") : null;
  if (f) f.value = FORMATADORES[f.className.split(" ").find(function (c) { return FORMATADORES[c]; })](f.value);
});

// ---------- abas ----------
var abas = [
  { botao: document.getElementById("btn-aba-alunos"), painel: document.getElementById("painel-alunos") },
  { botao: document.getElementById("btn-aba-docentes"), painel: document.getElementById("painel-docentes") }
];

abas.forEach(function (aba) {
  aba.botao.addEventListener("click", function () {
    abas.forEach(function (outra) {
      var ativa = outra === aba;
      outra.botao.classList.toggle("ativa", ativa);
      outra.botao.setAttribute("aria-selected", ativa ? "true" : "false");
      outra.painel.classList.toggle("oculto", !ativa);
    });
  });
});

function abaAtiva() {
  return abas.find(function (a) { return a.botao.classList.contains("ativa"); });
}

function abaDaAtual() {
  var atual = abas.find(function (a) { return !a.painel.classList.contains("oculto"); });
  return atual ? atual.botao.textContent : "ALUNOS";
}

// ---------- envio ----------
document.querySelectorAll("form").forEach(function (form) {
  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var alvo = abaAtiva();
    var caixaErros = alvo.painel.querySelector(".erros");
    caixaErros.textContent = "";

    var dados = {};
    new FormData(form).forEach(function (v, k) {
      dados[k] = typeof v === "string" ? v.trim() : v;
    });

    fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aba: form.dataset.aba, dados: dados })
    })
      .then(function (res) { return res.json(); })
      .then(function (resp) {
        if (!resp.ok) {
          caixaErros.textContent = resp.erros.join("\n");
          return;
        }
        document.getElementById("oficio").textContent = resp.oficio;
        document.getElementById("pagina-form").classList.add("oculto");
        document.getElementById("pagina-confirmacao").classList.remove("oculto");
        window.scrollTo(0, 0);
      });
  });
});

document.getElementById("voltar").addEventListener("click", function () {
  document.getElementById("pagina-confirmacao").classList.add("oculto");
  document.getElementById("pagina-form").classList.remove("oculto");
});
