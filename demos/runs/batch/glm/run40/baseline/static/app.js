function digitos(t) {
  return (t.match(/\d/g) || []).join("");
}

function formataMoeda(campo) {
  var d = digitos(campo.value);
  if (d === "") {
    campo.value = "";
    return;
  }
  var centavos = parseInt(d, 10);
  var parteInteira = Math.floor(centavos / 100);
  var cent = centavos % 100;
  var inteiraStr = String(parteInteira).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  campo.value = "R$ " + inteiraStr + "," + String(cent).padStart(2, "0");
}

function formataCpf(campo) {
  var d = digitos(campo.value).slice(0, 11);
  var r = d;
  if (d.length > 9) {
    r = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  } else if (d.length > 6) {
    r = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  } else if (d.length > 3) {
    r = d.slice(0, 3) + "." + d.slice(3);
  }
  campo.value = r;
}

function formataCep(campo) {
  var d = digitos(campo.value).slice(0, 8);
  if (d.length > 5) {
    campo.value = d.slice(0, 5) + "-" + d.slice(5);
  } else {
    campo.value = d;
  }
}

function formataData(campo) {
  var d = digitos(campo.value).slice(0, 8);
  if (d.length > 4) {
    campo.value = d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  } else if (d.length > 2) {
    campo.value = d.slice(0, 2) + "/" + d.slice(2);
  } else {
    campo.value = d;
  }
}

var FORMATA = {
  valor: formataMoeda,
  cpf: formataCpf,
  cep: formataCep,
  nascimento: formataData
};

var CAMPOS = [
  "nome", "nusp", "programa", "nivel", "tipo", "email", "evento",
  "periodo", "cidade", "estado", "pais", "link", "valor",
  "detalhamento", "apresentacao", "nascimento", "logradouro",
  "numero", "complemento", "bairro", "cep", "cidade-end",
  "estado-end", "cpf", "rg", "banco", "agencia", "conta"
];

function abreAba(aba) {
  document.getElementById("aba-alunos").classList.toggle("ativa", aba === "alunos");
  document.getElementById("aba-docentes").classList.toggle("ativa", aba === "docentes");
  document.getElementById("aba-alunos").setAttribute("aria-selected", aba === "alunos");
  document.getElementById("aba-docentes").setAttribute("aria-selected", aba === "docentes");
  document.getElementById("form-alunos").classList.toggle("visivel", aba === "alunos");
  document.getElementById("form-docentes").classList.toggle("visivel", aba === "docentes");
}

document.getElementById("aba-alunos").addEventListener("click", function () { abreAba("alunos"); });
document.getElementById("aba-docentes").addEventListener("click", function () { abreAba("docentes"); });

CAMPOS.forEach(function (nome) {
  var a = document.getElementById("a-" + nome);
  var d = document.getElementById("d-" + nome);
  [a, d].forEach(function (campo) {
    if (!campo) {
      return;
    }
    var tipo = nome.replace("-end", "");
    if (FORMATA[tipo]) {
      campo.addEventListener("blur", function () { FORMATA[tipo](campo); });
    }
  });
});

function montaCorpo(aba) {
  var dados = { aba: aba === "alunos" ? "alunos" : "docentes" };
  var mapa = {
    nome: "nome", nusp: "nusp", programa: "programa", nivel: "nivel",
    tipo: "tipo_auxilio", email: "email", evento: "evento",
    periodo: "periodo", cidade: "cidade_evento", estado: "estado_evento",
    pais: "pais_evento", link: "link_evento", valor: "valor",
    detalhamento: "detalhamento", apresentacao: "apresentacao",
    nascimento: "nascimento", logradouro: "logradouro",
    numero: "numero", complemento: "complemento", bairro: "bairro",
    cep: "cep", "cidade-end": "cidade", "estado-end": "estado",
    cpf: "cpf", rg: "rg", banco: "banco", agencia: "agencia", conta: "conta"
  };
  Object.keys(mapa).forEach(function (nome) {
    var campo = document.getElementById((aba === "alunos" ? "a-" : "d-") + nome);
    if (campo) {
      dados[mapa[nome]] = campo.value;
    } else {
      dados[mapa[nome]] = "";
    }
  });
  return dados;
}

function mostraErros(aba, erros) {
  var div = document.getElementById("erros-" + aba);
  div.innerHTML = "";
  erros.forEach(function (msg) {
    var p = document.createElement("p");
    p.textContent = msg;
    div.appendChild(p);
  });
}

function envia(form, aba) {
  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    fetch("/api/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(montaCorpo(aba))
    })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (!res.ok) {
          mostraErros(aba, res.erros);
          return;
        }
        document.getElementById("formulario").classList.add("oculto");
        var conf = document.getElementById("confirmacao");
        document.getElementById("oficio").textContent = res.oficio;
        conf.classList.remove("oculto");
        window.scrollTo(0, 0);
      });
  });
}

envia(document.getElementById("form-alunos"), "alunos");
envia(document.getElementById("form-docentes"), "docentes");
