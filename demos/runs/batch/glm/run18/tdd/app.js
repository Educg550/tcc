function formatarMoeda(campo) {
  var digitos = campo.value.replace(/\D/g, "");
  if (!digitos) {
    campo.value = "";
    return;
  }
  digitos = digitos.replace(/^0+/, "") || "0";
  var texto = digitos.padStart(3, "0");
  var reais = texto.slice(0, -2);
  var centavos = texto.slice(-2);
  var grupos = [];
  while (reais.length > 3) {
    grupos.unshift(reais.slice(-3));
    reais = reais.slice(0, -3);
  }
  grupos.unshift(reais);
  campo.value = "R$ " + grupos.join(".") + "," + centavos;
}

function formatarCPF(campo) {
  var d = campo.value.replace(/\D/g, "").slice(0, 11);
  if (d.length > 9) {
    campo.value = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  } else if (d.length > 6) {
    campo.value = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  } else if (d.length > 3) {
    campo.value = d.slice(0, 3) + "." + d.slice(3);
  } else {
    campo.value = d;
  }
}

function formatarCEP(campo) {
  var d = campo.value.replace(/\D/g, "").slice(0, 8);
  campo.value = d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(campo) {
  var d = campo.value.replace(/\D/g, "").slice(0, 8);
  if (d.length > 4) {
    campo.value = d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  } else if (d.length > 2) {
    campo.value = d.slice(0, 2) + "/" + d.slice(2);
  } else {
    campo.value = d;
  }
}

function validarCPF(cpf) {
  var d = cpf.replace(/\D/g, "");
  if (d.length !== 11) {
    return false;
  }
  var soma = 0;
  for (var i = 0; i < 9; i++) {
    soma += parseInt(d[i]) * (10 - i);
  }
  var dig1 = (soma * 10) % 11 % 10;
  if (dig1 !== parseInt(d[9])) {
    return false;
  }
  soma = 0;
  for (var j = 0; j < 10; j++) {
    soma += parseInt(d[j]) * (11 - j);
  }
  var dig2 = (soma * 10) % 11 % 10;
  return dig2 === parseInt(d[10]);
}

function trocarAba(alvo) {
  var ativa = document.querySelector(".aba.ativa");
  if (ativa) {
    ativa.classList.remove("ativa");
  }
  document.getElementById("aba-" + alvo).classList.add("ativa");
  document.getElementById("form-alunos").hidden = alvo !== "alunos";
  document.getElementById("form-docentes").hidden = alvo !== "docentes";
}

document.getElementById("aba-alunos").addEventListener("click", function () {
  trocarAba("alunos");
});
document.getElementById("aba-docentes").addEventListener("click", function () {
  trocarAba("docentes");
});

document.querySelectorAll(".moeda").forEach(function (c) {
  c.addEventListener("blur", function () { formatarMoeda(c); });
});
document.querySelectorAll(".cpf").forEach(function (c) {
  c.addEventListener("blur", function () { formatarCPF(c); });
});
document.querySelectorAll(".cep").forEach(function (c) {
  c.addEventListener("blur", function () { formatarCEP(c); });
});
document.querySelectorAll(".data").forEach(function (c) {
  c.addEventListener("blur", function () { formatarData(c); });
});

function coletar(form) {
  var dados = {};
  new FormData(form).forEach(function (v, k) {
    dados[k] = v;
  });
  return dados;
}

function mostrarErros(id, erros) {
  var caixa = document.getElementById(id);
  caixa.innerHTML = "";
  erros.forEach(function (e) {
    var p = document.createElement("p");
    p.textContent = e;
    caixa.appendChild(p);
  });
}

document.querySelectorAll(".formulario").forEach(function (form) {
  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var aba = form.id === "form-alunos" ? "alunos" : "docentes";
    var caixaId = aba === "alunos" ? "erros-alunos" : "erros-docentes";
    fetch("/enviar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aba: aba, campos: coletar(form) })
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
      if (!res.ok) {
        mostrarErros(caixaId, res.erros);
        return;
      }
      document.getElementById("oficio").textContent = res.oficio;
      document.getElementById("pagina").hidden = true;
      document.getElementById("confirmacao").hidden = false;
    });
  });
});
