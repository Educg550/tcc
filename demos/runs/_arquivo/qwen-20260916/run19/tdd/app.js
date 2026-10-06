function onlyDigits(s) { return (s || "").replace(/\D/g, ""); }

function formatValor(raw) {
  var d = onlyDigits(raw);
  var cents = parseInt(d || "0", 10);
  var inteiro = Math.floor(cents / 100);
  var resto = cents % 100;
  var s = String(inteiro);
  while (s.length > 3) { s = s.slice(0, -3) + "." + s.slice(-3); }
  return "R$ " + s + "," + String(resto).padStart(2, "0");
}

function formatCpf(raw) {
  var d = onlyDigits(raw).slice(0, 11);
  var out = "";
  for (var i = 0; i < d.length; i++) {
    if (i === 3 || i === 6) out += ".";
    if (i === 9) out += "-";
    out += d[i];
  }
  return out;
}

function formatCep(raw) {
  var d = onlyDigits(raw).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatData(raw) {
  var d = onlyDigits(raw).slice(0, 8);
  return d.replace(/(\d{2})(\d{2})(\d{2})(\d{2})/, "$1/$2/$3/$4").replace(/(\d{2})(\d{2})$/, "$1/$2");
}

function formatarData(raw) {
  var d = onlyDigits(raw).slice(0, 8);
  var partes = [];
  for (var i = 0; i < d.length; i += 2) { partes.push(d.slice(i, i + 2)); }
  return partes.join("/");
}

var FORMATADORES = {
  valor_solicitado: formatValor,
  cpf: formatCpf,
  cep: formatCep,
  data_nascimento: formatarData
};

function soNumeros(s) { return /^[0-9]+$/.test(s); }

function cpfValidoFormato(s) { return /^[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}$/.test(s); }

function cpfValidosDigitos(s) {
  var d = onlyDigits(s);
  if (d.length !== 11) return false;
  for (var i = 9; i < 11; i++) {
    var soma = 0;
    for (var j = 0; j < i; j++) { soma += parseInt(d[j], 10) * (i + 1 - j); }
    var dig = (soma * 10) % 11 % 10;
    if (dig !== parseInt(d[i], 10)) return false;
  }
  return true;
}

function cepValidoFormato(s) { return /^[0-9]{5}-[0-9]{3}$/.test(s); }

function dataFormato(s) { return /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/.test(s); }

function dataValida(s) {
  var p = s.split("/");
  var dia = parseInt(p[0], 10), mes = parseInt(p[1], 10), ano = parseInt(p[2], 10);
  var dias = [31, (ano % 4 === 0 && (ano % 100 !== 0 || ano % 400 === 0)) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return mes >= 1 && mes <= 12 && dia >= 1 && dia <= dias[mes - 1];
}

function emailValido(s) {
  if (s.indexOf("@") < 0) return false;
  var dom = s.split("@").pop();
  return dom.length > 0 && dom.indexOf(".") > 0;
}

var OBRIGATORIOS_ALUNOS = ["nome_completo", "nusp", "programa", "nivel", "tipo_auxilio", "email", "nome_evento", "periodo_evento", "cidade_evento", "estado_evento", "pais_evento", "valor_solicitado", "detalhamento", "apresentar_trabalho", "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg_rnm", "nome_banco", "numero_agencia", "numero_conta"];
var OBRIGATORIOS_DOCENTES = ["nome_completo", "nusp", "programa", "email", "nome_evento", "periodo_evento", "cidade_evento", "estado_evento", "pais_evento", "valor_solicitado", "detalhamento", "apresentar_trabalho", "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg_rnm", "nome_banco", "numero_agencia", "numero_conta"];

function coletar(form) {
  var dados = {};
  var elems = form.querySelectorAll("input, select, textarea");
  for (var i = 0; i < elems.length; i++) { dados[elems[i].name] = elems[i].value; }
  return dados;
}

function validar(d, aba) {
  var erros = [];
  var obr = aba === "alunos" ? OBRIGATORIOS_ALUNOS : OBRIGATORIOS_DOCENTES;
  var faltando = false;
  for (var i = 0; i < obr.length; i++) { if (!(d[obr[i]] || "").trim()) { faltando = true; } }
  if (faltando) erros.push("Preencha todos os campos");
  if (d.nusp && !soNumeros(d.nusp)) erros.push("N. USP deve conter apenas números");
  if (d.numero_agencia && !soNumeros(d.numero_agencia)) erros.push("Número da agência deve conter apenas números");
  var v = onlyDigits(d.valor_solicitado);
  if (!v || parseInt(v, 10) <= 0) erros.push("Valor solicitado deve ser maior que 0");
  if (d.email && !emailValido(d.email)) erros.push("E-mail inválido");
  if (d.cpf) { if (!cpfValidoFormato(d.cpf)) erros.push("CPF deve estar no formato 000.000.000-00"); else if (!cpfValidosDigitos(d.cpf)) erros.push("CPF inválido"); }
  if (d.cep && !cepValidoFormato(d.cep)) erros.push("CEP deve estar no formato 00000-000");
  if (d.data_nascimento) { if (!dataFormato(d.data_nascimento)) erros.push("Data de nascimento deve estar no formato dd/mm/aaaa"); else if (!dataValida(d.data_nascimento)) erros.push("Data de nascimento inválida"); }
  return erros;
}

function mostrarErros(lista) {
  var box = document.getElementById("erros");
  if (!lista.length) { box.hidden = true; box.textContent = ""; return; }
  box.hidden = false;
  box.textContent = lista.join("\n");
}

function coletarPayload(form, aba) {
  var d = coletar(form);
  d.aba = aba;
  return d;
}

function enviar(form, aba) {
  var dados = coletarPayload(form, aba);
  var erros = validar(dados, aba);
  if (erros.length) { mostrarErros(erros); return; }
  fetch("/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados)
  })
  .then(function (r) { return r.json(); })
  .then(function (res) {
    if (res.errors && res.errors.length) { mostrarErros(res.errors); return; }
    mostrarErros([]);
    document.querySelectorAll(".formulario").forEach(function (f) { f.classList.remove("ativo"); });
    document.querySelector(".abas").style.display = "none";
    var conf = document.getElementById("confirmacao");
    conf.hidden = false;
    document.getElementById("oficio").textContent = res.oficio;
  });
}

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".aba").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".aba").forEach(function (b) { b.classList.remove("ativa"); });
      document.querySelectorAll(".formulario").forEach(function (f) { f.classList.remove("ativo"); });
      btn.classList.add("ativa");
      document.getElementById(btn.dataset.alvo).classList.add("ativo");
      mostrarErros([]);
    });
  });

  document.querySelectorAll(".formulario").forEach(function (form) {
    Object.keys(FORMATADORES).forEach(function (nome) {
      var campo = form.querySelector('[name="' + nome + '"]');
      if (campo) {
        campo.addEventListener("blur", function () { campo.value = FORMATADORES[nome](campo.value); });
      }
    });
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      enviar(form, form.id === "form-alunos" ? "alunos" : "docentes");
    });
  });
});

// Mensagens de erro (referência): Preencha todos os campos, N. USP deve conter apenas números,
// Número da agência deve conter apenas números, Valor solicitado deve ser maior que 0,
// E-mail inválido, CPF deve estar no formato 000.000.000-00, CEP deve estar no formato 00000-000,
// Data de nascimento deve estar no formato dd/mm/aaaa, CPF inválido, Data de nascimento inválida.
// Tela de confirmação: "Solicitação registrada".
