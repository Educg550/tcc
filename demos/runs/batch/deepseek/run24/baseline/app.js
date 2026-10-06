function formatarValor(v) {
  var d = v.replace(/\D/g, "");
  if (d === "") return "";
  while (d.length < 3) d = "0" + d;
  var centavos = d.slice(-2);
  var inteiros = d.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + inteiros + "," + centavos;
}

function formatarCPF(v) {
  var d = v.replace(/\D/g, "").slice(0, 11);
  if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
  return d;
}

function formatarCEP(v) {
  var d = v.replace(/\D/g, "").slice(0, 8);
  if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
  return d;
}

function formatarData(v) {
  var d = v.replace(/\D/g, "").slice(0, 8);
  if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
  return d;
}

var FORMATOS = {
  valor: formatarValor,
  cpf: formatarCPF,
  cep: formatarCEP,
  nascimento: formatarData
};

Object.keys(FORMATOS).forEach(function (nome) {
  var fn = FORMATOS[nome];
  document.querySelectorAll('input[name="' + nome + '"]').forEach(function (el) {
    el.addEventListener("blur", function () {
      el.value = fn(el.value);
    });
  });
});

var abas = document.querySelectorAll(".aba");
var formAlunos = document.getElementById("form-alunos");
var formDocentes = document.getElementById("form-docentes");

abas.forEach(function (btn) {
  btn.addEventListener("click", function () {
    abas.forEach(function (b) { b.classList.remove("ativa"); });
    btn.classList.add("ativa");
    var alvo = btn.dataset.aba;
    formAlunos.hidden = alvo !== "alunos";
    formDocentes.hidden = alvo !== "docentes";
  });
});

async function enviar(form) {
  var dados = { aba: form.dataset.aba };
  form.querySelectorAll("input[name], select[name], textarea[name]").forEach(function (el) {
    dados[el.name] = el.value;
  });

  var resp = await fetch("/api/solicitar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados)
  });
  var json = await resp.json();

  var caixa = form.querySelector(".erros");
  if (json.erros && json.erros.length > 0) {
    caixa.innerHTML = json.erros
      .map(function (e) { return "<div>" + e + "</div>"; })
      .join("");
    caixa.hidden = false;
    return;
  }

  caixa.hidden = true;
  document.getElementById("abas").hidden = true;
  document.getElementById("formularios").hidden = true;
  document.getElementById("oficio").textContent = json.oficio;
  document.getElementById("confirmacao").hidden = false;
}

document.querySelectorAll("form").forEach(function (form) {
  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    enviar(form);
  });
});
