document.addEventListener("DOMContentLoaded", function() {
  var tabs = document.querySelectorAll(".tab");
  var contents = document.querySelectorAll(".tab-content");

  tabs.forEach(function(tab) {
    tab.addEventListener("click", function() {
      tabs.forEach(function(t) { t.classList.remove("active"); });
      tab.classList.add("active");
      contents.forEach(function(c) { c.style.display = "none"; });
      var target = document.getElementById(tab.dataset.tab + "-content");
      if (target) target.style.display = "block";
      document.getElementById("confirmation").style.display = "none";
      document.querySelectorAll(".form-container").forEach(function(f) { f.style.display = ""; });
      document.querySelector(".tabs").style.display = "";
    });
  });

  // Máscaras de formatação
  function formatCPF(input) {
    var v = input.value.replace(/\D/g, "").slice(0, 11);
    var out = v;
    if (v.length > 9) out = v.slice(0,3)+"."+v.slice(3,6)+"."+v.slice(6,9)+"-"+v.slice(9,11);
    else if (v.length > 6) out = v.slice(0,3)+"."+v.slice(3,6)+"."+v.slice(6);
    else if (v.length > 3) out = v.slice(0,3)+"."+v.slice(3);
    input.value = out;
  }

  function formatCEP(input) {
    var v = input.value.replace(/\D/g, "").slice(0, 8);
    if (v.length > 5) v = v.slice(0,5)+"-"+v.slice(5);
    input.value = v;
  }

  function formatData(input) {
    var v = input.value.replace(/\D/g, "").slice(0, 8);
    var out = v;
    if (v.length > 4) out = v.slice(0,2)+"/"+v.slice(2,4)+"/"+v.slice(4);
    else if (v.length > 2) out = v.slice(0,2)+"/"+v.slice(2);
    input.value = out;
  }

  function formatValor(input) {
    var v = input.value.replace(/\D/g, "");
    if (!v) { input.value = ""; return; }
    var centavos = parseInt(v, 10);
    var reais = Math.floor(centavos / 100);
    var c = centavos % 100;
    var s = reais.toString();
    // Adicionar pontos de milhar
    var parts = [];
    while (s.length > 3) {
      parts.push(s.slice(-3));
      s = s.slice(0, -3);
    }
    parts.push(s);
    s = parts.reverse().join(".");
    input.value = "R$ " + s + "," + (c < 10 ? "0" : "") + c;
  }

  function applyMasks(form) {
    form.querySelectorAll("input[name='cpf']").forEach(function(el) { el.addEventListener("blur", function() { formatCPF(el); }); });
    form.querySelectorAll("input[name='cep']").forEach(function(el) { el.addEventListener("blur", function() { formatCEP(el); }); });
    form.querySelectorAll("input[name='data_nascimento']").forEach(function(el) { el.addEventListener("blur", function() { formatData(el); }); });
    form.querySelectorAll("input[name='valor']").forEach(function(el) { el.addEventListener("blur", function() { formatValor(el); }); });
  }

  document.getElementById("form-alunos") && applyMasks(document.getElementById("form-alunos"));
  document.getElementById("form-docentes") && applyMasks(document.getElementById("form-docentes"));

  // Submit handler
  function extractFormData(form, isStudent) {
    var data = {};
    form.querySelectorAll("[name]").forEach(function(el) {
      data[el.name] = el.value.trim();
    });
    // Convert valor back to centavos
    var valorStr = (data.valor || "").replace(/[^\d]/g, "");
    data.valor = valorStr ? parseInt(valorStr, 10) : 0;
    return data;
  }

  function showErrors(aba, erros) {
    var errDiv = document.getElementById(aba + "-errors");
    errDiv.innerHTML = "";
    erros.forEach(function(e) {
      var p = document.createElement("div");
      p.textContent = e;
      errDiv.appendChild(p);
    });
  }

  function handleSubmit(tipo, formId) {
    var form = document.getElementById(formId);
    if (!form) return;
    form.addEventListener("submit", function(ev) {
      ev.preventDefault();
      var data = extractFormData(form, tipo === "aluno");
      fetch("/api/solicitacoes/" + tipo, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      }).then(function(r) { return r.json(); }).then(function(res) {
        if (res.ok) {
          document.getElementById("form-alunos").parentElement.style.display = "none";
          document.getElementById("form-docentes").parentElement.style.display = "none";
          document.querySelector(".tabs").style.display = "none";
          document.getElementById("confirmation").style.display = "block";
          document.getElementById("oficio-text").textContent = res.oficio;
          window.scrollTo(0, 0);
        } else {
          var aba = tipo === "aluno" ? "alunos" : "docentes";
          showErrors(aba, res.erros);
        }
      });
    });
  }

  handleSubmit("aluno", "form-alunos");
  handleSubmit("docente", "form-docentes");
});
