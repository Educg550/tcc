function formatCep(v) {
  return v.replace(/\D/g, "").replace(/(\d{5})(\d)/, "$1-$2");
}

function formatCpf(v) {
  return v.replace(/\D/g, "").replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d{1,2})$/, "$1-$2");
}

function formatData(v) {
  return v.replace(/\D/g, "").replace(/(\d{2})(\d)/, "$1/$2").replace(/(\d{2})\/(\d{2})(\d)/, "$1/$2/$3");
}

function formatValor(v) {
  var digits = v.replace(/\D/g, "");
  if (!digits) return "";
  var cents = parseInt(digits, 10);
  var s = String(cents).padStart(3, "0");
  var inteiro = s.slice(0, -2);
  var dec = s.slice(-2);
  inteiro = String(parseInt(inteiro, 10));
  var formatted = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + formatted + "," + dec;
}

function maskCep(el) {
  el.value = formatCep(el.value);
}

function maskCpf(el) {
  el.value = formatCpf(el.value);
}

function maskData(el) {
  el.value = formatData(el.value);
}

function maskValor(el) {
  el.value = formatValor(el.value);
}

function validateCPF(cpf) {
  var d = cpf.replace(/\D/g, "");
  if (d.length !== 11 || d === d[0].repeat(11)) return false;
  var s = 0;
  for (var i = 0; i < 9; i++) s += parseInt(d[i]) * (10 - i);
  var d1 = (s * 10) % 11;
  if (d1 === 10) d1 = 0;
  if (d1 !== parseInt(d[9])) return false;
  s = 0;
  for (var j = 0; j < 10; j++) s += parseInt(d[j]) * (11 - j);
  var d2 = (s * 10) % 11;
  if (d2 === 10) d2 = 0;
  return d2 === parseInt(d[10]);
}

function validateDate(dt) {
  var m = dt.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return false;
  var d = parseInt(m[1], 10), mo = parseInt(m[2], 10), y = parseInt(m[3], 10);
  if (mo < 1 || mo > 12) return false;
  var days = new Date(y, mo, 0).getDate();
  return d >= 1 && d <= days;
}

function getFormData(form) {
  var data = {};
  form.querySelectorAll("[name]").forEach(function (el) {
    var val = el.value.trim();
    data[el.name] = val;
  });
  var v = (data.valor_solicitado || "").replace(/\D/g, "");
  data.valor_solicitado = v ? parseInt(v, 10) : "";
  return data;
}

function validateForm(data, aba) {
  var errors = [];
  var required = ["nome_completo", "nusp", "programa", "email", "nome_evento", "periodo_evento", "cidade_evento", "estado_evento", "pais_evento", "valor_solicitado", "detalhamento", "apresenta_trabalho", "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta"];
  if (aba === "alunos") required.push("nivel", "tipo_auxilio");
  var hasEmpty = required.some(function (k) {
    return !String(data[k] || "").trim();
  });
  if (hasEmpty) errors.push("Preencha todos os campos");
  if (data.nusp && !/^\d+$/.test(data.nusp)) errors.push("N. USP deve conter apenas números");
  if (data.agencia && !/^\d+$/.test(String(data.agencia))) errors.push("Número da agência deve conter apenas números");
  var valor = data.valor_solicitado;
  if (typeof valor === "number" && (valor <= 0 || valor > 999999999)) errors.push("Valor solicitado deve ser maior que 0");
  if (data.email && (!/@/.test(data.email) || !/\./.test(data.email.split("@")[1] || ""))) errors.push("E-mail inválido");
  if (data.cpf) {
    if (!/^\d{3}\.\d{3}\.\d{3}-\d{2}$/.test(data.cpf)) errors.push("CPF deve estar no formato 000.000.000-00");
    else if (!validateCPF(data.cpf)) errors.push("CPF inválido");
  }
  if (data.cep && !/^\d{5}-\d{3}$/.test(data.cep)) errors.push("CEP deve estar no formato 00000-000");
  if (data.data_nascimento) {
    if (!/^\d{2}\/\d{2}\/\d{4}$/.test(data.data_nascimento)) errors.push("Data de nascimento deve estar no formato dd/mm/aaaa");
    else if (!validateDate(data.data_nascimento)) errors.push("Data de nascimento inválida");
  }
  return errors;
}

document.addEventListener("DOMContentLoaded", function () {
  var tabs = document.querySelectorAll(".tab");
  var forms = document.querySelectorAll(".form");
  var errorsBox = document.getElementById("errors");
  var confirmation = document.querySelector(".confirmation");
  var formsSection = document.querySelector(".forms");

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      var which = tab.dataset.tab;
      tabs.forEach(function (t) { t.classList.remove("active"); });
      tab.classList.add("active");
      forms.forEach(function (f) {
        f.style.display = f.classList.contains(which) ? "grid" : "none";
      });
      errorsBox.classList.remove("show");
    });
  });

  forms.forEach(function (form) {
    var cep = form.querySelector('[name="cep"]');
    var cpf = form.querySelector('[name="cpf"]');
    var dnasc = form.querySelector('[name="data_nascimento"]');
    var valor = form.querySelector('[name="valor_solicitado"]');

    if (cep) cep.addEventListener("blur", function () { maskCep(cep); });
    if (cpf) cpf.addEventListener("blur", function () { maskCpf(cpf); });
    if (dnasc) dnasc.addEventListener("blur", function () { maskData(dnasc); });
    if (valor) valor.addEventListener("blur", function () { maskValor(valor); });
    valor && valor.addEventListener("input", function () { valor.value = valor.value.replace(/[^0-9R$,\s.]/g, ""); });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var aba = form.classList.contains("alunos") ? "alunos" : "docentes";
      var data = getFormData(form);
      var errors = validateForm(data, aba);

      if (errors.length) {
        errorsBox.innerHTML = "";
        errors.forEach(function (err) {
          var div = document.createElement("div");
          div.textContent = err;
          errorsBox.appendChild(div);
        });
        errorsBox.classList.add("show");
        return;
      }

      data.aba = aba;

      fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      })
        .then(function (r) { return r.json().then(function (j) { return { status: r.status, body: j }; }); })
        .then(function (res) {
          if (res.status === 422) {
            var list = Array.isArray(res.body.detail) ? res.body.detail : [res.body.detail];
            errorsBox.innerHTML = "";
            list.forEach(function (err) {
              var div = document.createElement("div");
              div.textContent = err;
              errorsBox.appendChild(div);
            });
            errorsBox.classList.add("show");
          } else if (res.status === 200) {
            errorsBox.classList.remove("show");
            formsSection.style.display = "none";
            document.querySelector(".tabs").style.display = "none";
            confirmation.style.display = "block";
            document.getElementById("oficio").textContent = res.body.oficio;
          }
        });
    });
  });
});
