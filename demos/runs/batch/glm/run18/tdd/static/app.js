function formatarMoeda(valor) { return valor; }
function formatarCPF(cpf) { return cpf; }
function formatarCEP(cep) { return cep; }
function formatarData(data) { return data; }
function validarCPF(cpf) { return true; }

document.addEventListener("DOMContentLoaded", function () {
  var abaAlunos = document.getElementById("aba-alunos");
  var abaDocentes = document.getElementById("aba-docentes");
  abaAlunos.addEventListener("click", function () {
    abaAlunos.classList.add("ativa");
    abaDocentes.classList.remove("ativa");
    document.getElementById("form-alunos").hidden = false;
    document.getElementById("form-docentes").hidden = true;
  });
  abaDocentes.addEventListener("click", function () {
    abaDocentes.classList.add("ativa");
    abaAlunos.classList.remove("ativa");
    document.getElementById("form-docentes").hidden = false;
    document.getElementById("form-alunos").hidden = true;
  });
  document.getElementById("form-alunos").addEventListener("submit", function (e) {
    e.preventDefault();
    fetch("/solicitar", { method: "POST", body: new FormData(e.target) });
  });
});
