document.addEventListener("DOMContentLoaded", function () {
  var forms = Array.prototype.slice.call(document.querySelectorAll(".form-container"));
  var tabBtns = Array.prototype.slice.call(document.querySelectorAll(".tab-btn"));
  var main = document.querySelector("main");

  function mostrarFormulario() {
    tabBtns.forEach(function (b) { b.style.display = ""; });
    forms.forEach(function (f) { f.style.display = ""; });
  }

  function ativar(t) {
    tabBtns.forEach(function (b) {
      var ativo = b.getAttribute("data-tab") === t;
      b.classList.toggle("active", ativo);
      b.setAttribute("aria-selected", ativo ? "true" : "false");
    });
    forms.forEach(function (f) {
      f.classList.toggle("active", f.getAttribute("data-aba") === t);
    });
  }

  tabBtns.forEach(function (b) {
    b.addEventListener("click", function () {
      mostrarFormulario();
      ativar(b.getAttribute("data-tab"));
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll("[data-format]"), function (input) {
    input.addEventListener("blur", function () {
      var d = input.value.replace(/\D/g, "");
      switch (input.getAttribute("data-format")) {
        case "moeda":
          if (d) {
            var n = BigInt(d), i = n / 100n, c = Number(n % 100n), s = i.toString(), r = "", k = 0;
            for (var x = s.length - 1; x >= 0; x--) { r = s[x] + r; if (++k % 3 === 0 && x > 0) r = "." + r; }
            input.value = "R$ " + r + "," + String(c).padStart(2, "0");
          } else { input.value = ""; }
          break;
        case "cpf":
          if (d) { var v = d.slice(0, 11); input.value = v.slice(0, 3) + "." + v.slice(3, 6) + "." + v.slice(6, 9) + "-" + v.slice(9); } else { input.value = ""; }
          break;
        case "cep":
          if (d) { var c2 = d.slice(0, 8); input.value = c2.slice(0, 5) + "-" + c2.slice(5); } else { input.value = ""; }
          break;
        case "data":
          if (d) { var dt = d.slice(0, 8); input.value = dt.slice(0, 2) + "/" + dt.slice(2, 4) + "/" + dt.slice(4); } else { input.value = ""; }
          break;
      }
    });
  });

  forms.forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var fd = new FormData(form);
      var aba = form.getAttribute("data-aba");
      fd.set("aba", aba);
      var errosBox = form.querySelector(".errors-container");
      if (errosBox) { errosBox.textContent = ""; }

      fetch("/solicitacao", { method: "POST", body: fd })
        .then(function (r) {
          return r.text().then(function (t) { return { status: r.status, body: t }; });
        })
        .then(function (res) {
          if (res.status === 200) {
            mostrarConfirmacao(res.body);
          } else {
            mostrarFormulario();
            ativar(aba);
            if (errosBox) {
              errosBox.textContent = res.body;
            }
            form.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        });
    });
  });

  function mostrarConfirmacao(oficio) {
    tabBtns.forEach(function (b) { b.style.display = "none"; });
    forms.forEach(function (f) { f.style.display = "none"; });
    var el = document.createElement("section");
    el.className = "confirmacao";
    el.innerHTML = '<h2>Solicitação registrada</h2>' +
      '<pre class="oficio"></pre>' +
      '<button type="button" class="btn-voltar">Voltar ao formulário</button>';
    el.querySelector(".oficio").textContent = oficio;
    el.querySelector(".btn-voltar").addEventListener("click", function () {
      el.remove();
      mostrarFormulario();
      ativar("alunos");
    });
    main.innerHTML = "";
    main.appendChild(el);
    main.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  ativar("alunos");
});
