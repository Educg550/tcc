function formatarValorMoeda(valor) {
  var digitos = (valor || "").replace(/[^0-9]/g, "");
  if (!digitos) return "";
  var n = BigInt(digitos);
  var reais = n / 100n;
  var centavos = n % 100n;
  var s = reais.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  var c = centavos.toString().padStart(2, "0");
  return "R$ " + s + "," + c;
}

function formatarCPF(valor) {
  var d = (valor || "").replace(/[^0-9]/g, "").slice(0, 11);
  d = d.replace(/(\d{3})(\d{1,})/, "$1.$2");
  d = d.replace(/(\d{3}\.\d{3})(\d{1,})/, "$1.$2");
  d = d.replace(/(\d{3}\.\d{3}\.\d{3})(\d{1,})/, "$1-$2");
  return d;
}

function formatarCEP(valor) {
  var d = (valor || "").replace(/[^0-9]/g, "").slice(0, 8);
  return d.replace(/(\d{5})(\d{1,})/, "$1-$2");
}

function formatarData(valor) {
  var d = (valor || "").replace(/[^0-9]/g, "").slice(0, 8);
  d = d.replace(/(\d{2})(\d{1,})/, "$1/$2");
  d = d.replace(/(\d{2}\/\d{2})(\d{1,})/, "$1/$2");
  return d;
}

window.formatarValorMoeda = formatarValorMoeda;
window.formatarCPF = formatarCPF;
window.formatarCEP = formatarCEP;
window.formatarData = formatarData;

(function () {
  var FORMAT = {
    valor: formatarValorMoeda,
    cpf: formatarCPF,
    cep: formatarCEP,
    data_nascimento: formatarData
  };

  document.querySelectorAll("form").forEach(function (form) {
    Object.keys(FORMAT).forEach(function (name) {
      var input = form.querySelector('[name="' + name + '"]');
      if (input) {
        input.addEventListener("blur", function () {
          input.value = FORMAT[name](input.value);
        });
      }
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var aba = form.getAttribute("data-aba");
      var dados = { aba: aba };
      form.querySelectorAll("input, select, textarea").forEach(function (el) {
        dados[el.name] = el.value;
      });

      fetch("/api/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (r) { return r.json(); })
        .then(function (res) {
          var lista = document.getElementById("erros-" + aba);
          lista.innerHTML = "";
          (res.errors || []).forEach(function (m) {
            var li = document.createElement("li");
            li.textContent = m;
            lista.appendChild(li);
          });
          if (res.oficio) {
            document.getElementById("oficio").textContent = res.oficio;
            document.getElementById("form-page").classList.add("oculto");
            document.getElementById("confirmacao").classList.remove("oculto");
          }
        });
    });
  });

  var abas = document.querySelectorAll(".aba");
  abas.forEach(function (btn) {
    btn.addEventListener("click", function () {
      abas.forEach(function (b) {
        var ativo = b === btn;
        b.setAttribute("aria-selected", ativo ? "true" : "false");
        b.classList.toggle("ativa", ativo);
      });
      document.querySelectorAll(".painel").forEach(function (p) {
        p.classList.toggle("oculto", p.id !== "painel-" + btn.dataset.tab);
      });
    });
  });
})();
