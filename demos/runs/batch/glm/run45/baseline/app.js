"use strict";

const abas = { alunos: document.getElementById("aba-alunos"), docentes: document.getElementById("aba-docentes") };
const formularios = { alunos: document.getElementById("form-alunos"), docentes: document.getElementById("form-docentes") };
const errosDivs = { alunos: document.getElementById("erros-alunos"), docentes: document.getElementById("erros-docentes") };

function mostrarAba(nome) {
    for (const chave of ["alunos", "docentes"]) {
        const ativa = chave === nome;
        abas[chave].classList.toggle("ativa", ativa);
        abas[chave].setAttribute("aria-selected", String(ativa));
        formularios[chave].hidden = !ativa;
        if (!ativa) {
            errosDivs[chave].hidden = true;
        }
    }
}

abas.alunos.addEventListener("click", () => mostrarAba("alunos"));
abas.docentes.addEventListener("click", () => mostrarAba("docentes"));

function aoSairFormata(event) {
    const campo = event.target;
    if (campo.dataset.formato === undefined) {
        return;
    }
    const digitos = campo.value.replace(/\D/g, "");
    let formatado = "";
    if (campo.dataset.formato === "valor") {
        formatado = digitos.length ? formatarValor(digitos) : "";
    } else if (campo.dataset.formato === "cpf") {
        formatado = formatarCpf(digitos);
    } else if (campo.dataset.formato === "cep") {
        formatado = formatarCep(digitos);
    } else if (campo.dataset.formato === "data") {
        formatado = formatarData(digitos);
    }
    campo.value = formatado;
}

function formatarValor(digitos) {
    const centavos = parseInt(digitos, 10);
    const texto = centavos.toLocaleString("pt-BR");
    return "R$ " + texto + ",00";
}

function formatarCpf(digitos) {
    const d = digitos.slice(0, 11);
    let saida = d.slice(0, 3);
    if (d.length > 3) saida += "." + d.slice(3, 6);
    if (d.length > 6) saida += "." + d.slice(6, 9);
    if (d.length > 9) saida += "-" + d.slice(9);
    return saida;
}

function formatarCep(digitos) {
    const d = digitos.slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(digitos) {
    const d = digitos.slice(0, 8);
    let saida = d.slice(0, 2);
    if (d.length > 2) saida += "/" + d.slice(2, 4);
    if (d.length > 4) saida += "/" + d.slice(4);
    return saida;
}

for (const campo of document.querySelectorAll("input[data-formato]")) {
    campo.addEventListener("blur", aoSairFormata);
}

for (const nome of ["alunos", "docentes"]) {
    const form = formularios[nome];
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const errosDiv = errosDivs[nome];
        errosDiv.replaceChildren();
        const dados = coletarDados(form);
        try {
            const resposta = await fetch("/api/solicitar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tipo: nome, dados: dados }),
            });
            if (!resposta.ok) {
                throw new Error();
            }
            const resultado = await resposta.json();
            if (resultado.ok) {
                document.getElementById("cabecalho").scrollIntoView();
                document.getElementById("oficio").textContent = resultado.oficio;
                document.getElementById("confirmacao").hidden = false;
                for (const chave of ["alunos", "docentes"]) {
                    formularios[chave].hidden = true;
                    abas[chave].style.display = "none";
                }
            } else {
                for (const mensagem of resultado.erros) {
                    const linha = document.createElement("p");
                    linha.textContent = mensagem;
                    errosDiv.append(linha);
                }
                errosDiv.hidden = false;
            }
        } catch (erro) {
            const linha = document.createElement("p");
            linha.textContent = "Não foi possível enviar a solicitação";
            errosDiv.append(linha);
            errosDiv.hidden = false;
        }
    });
}

function coletarDados(form) {
    const dados = {};
    for (const elemento of form.querySelectorAll("[name]")) {
        dados[elemento.name] = elemento.value;
    }
    dados.valor = dados.valor.replace(/\D/g, "");
    return dados;
}