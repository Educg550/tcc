// Alternância de abas e formatação de campos.

document.querySelectorAll(".aba").forEach(function (botao) {
  botao.addEventListener("click", function () {
    var aba = botao.getAttribute("data-aba");
    document.querySelectorAll(".aba").forEach(function (b) {
      b.classList.toggle("ativa", b === botao);
    });
    document.getElementById("form-alunos").classList.toggle("visivel", aba === "alunos");
    document.getElementById("form-docentes").classList.toggle("visivel", aba === "docentes");
  });
});

function formatarMoeda(digitos) {
  if (!digitos) return "";
  var reais = Math.floor(Number(digitos) / 100);
  var centavos = String(Number(digitos) % 100).padStart(2, "0");
  var partes = String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + partes + "," + centavos;
}

function formatarCpf(d) {
  return d.length === 11 ? d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9) : d;
}

function formatarCep(d) {
  return d.length === 8 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(d) {
  return d.length === 8 ? d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4) : d;
}

function soDigitos(valor) {
  return valor.replace(/\D/g, "");
}

function aplicar(formatador) {
  return function (evento) {
    if (evento.target.value) {
      evento.target.value = formatador(soDigitos(evento.target.value));
    }
  };
}

document.querySelectorAll(".moeda").forEach(function (campo) {
  campo.addEventListener("blur", aplicar(formatarMoeda));
});
document.querySelectorAll(".cpf").forEach(function (campo) {
  campo.addEventListener("blur", aplicar(formatarCpf));
});
document.querySelectorAll(".cep").forEach(function (campo) {
  campo.addEventListener("blur", aplicar(formatarCep));
});
document.querySelectorAll(".data").forEach(function (campo) {
  campo.addEventListener("blur", aplicar(formatarData));
});
