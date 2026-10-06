function soDigitos(v) {
  return v.replace(/\D/g, "");
}

function formatarMoeda(v) {
  var d = soDigitos(v);
  if (!d) return "";
  var centavos = BigInt(d);
  var inteiro = centavos / 100n;
  var cent = (centavos % 100n).toString().padStart(2, "0");
  var s = inteiro.toString();
  var comPontos = "";
  while (s.length > 3) {
    comPontos = "." + s.slice(-3) + comPontos;
    s = s.slice(0, -3);
  }
  comPontos = s + comPontos;
  return "R$ " + comPontos + "," + cent;
}

function formatarCpf(v) {
  var d = soDigitos(v).slice(0, 11);
  var s = d.slice(0, 3);
  if (d.length > 3) s += "." + d.slice(3, 6);
  if (d.length > 6) s += "." + d.slice(6, 9);
  if (d.length > 9) s += "-" + d.slice(9, 11);
  return s;
}

function formatarCep(v) {
  var d = soDigitos(v).slice(0, 8);
  if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
  return d;
}

function formatarData(v) {
  var d = soDigitos(v).slice(0, 8);
  var s = d.slice(0, 2);
  if (d.length > 2) s += "/" + d.slice(2, 4);
  if (d.length > 4) s += "/" + d.slice(4, 8);
  return s;
}

var FORMATADORES = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData
};

function extrairValor(input) {
  if (input.classList.contains("moeda")) return soDigitos(input.value);
  return input.value.trim();
}

document.querySelectorAll(".aba").forEach(function (aba) {
  aba.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (a) {
      a.classList.remove("ativa");
      a.setAttribute("aria-selected", "false");
    });
    aba.classList.add("ativa");
    aba.setAttribute("aria-selected", "true");
    document.querySelectorAll(".formulario").forEach(function (f) {
      f.classList.toggle("oculto", f.dataset.tipo !== aba.dataset.aba);
    });
  });
});

document.querySelectorAll(".formulario").forEach(function (form) {
  form.querySelectorAll("input").forEach(function (input) {
    for (var chave in FORMATADORES) {
      if (input.classList.contains(chave)) {
        input.addEventListener("blur", function () {
          input.value = FORMATADORES[chave](input.value);
        });
        break;
      }
    }
  });

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var box = form.querySelector(".erros");
    box.innerHTML = "";
    var dados = {};
    var elementos = Array.prototype.slice.call(form.elements);
    elementos.forEach(function (el) {
      if (el.name && typeof el.value === "string") {
        dados[el.name] = extrairValor(el);
      }
    });
    fetch("/solicitacao/" + form.dataset.tipo, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados)
    })
      .then(function (r) { return r.json(); })
      .then(function (resp) {
        if (!resp.ok) {
          resp.erros.forEach(function (e) {
            var p = document.createElement("p");
            p.textContent = e;
            box.appendChild(p);
          });
          return;
        }
        document.getElementById("oficio").textContent = resp.oficio;
        document.getElementById("tela-formulario").classList.add("oculto");
        document.getElementById("tela-oficio").classList.remove("oculto");
        document.body.classList.remove("sem-rolagem");
      });
  });
});

document.body.classList.add("sem-rolagem");
