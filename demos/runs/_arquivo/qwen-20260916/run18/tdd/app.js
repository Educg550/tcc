const camposAlunos = [
    {label: "SOLICITANTE E EVENTO", bloco: true},
    {label: "NOME COMPLETO - SEM ABREVIAR", nome: "nome", placeholder: "Maria da Silva"},
    {label: "N. USP", nome: "nusp", placeholder: "12345678"},
    {label: "PROGRAMA", nome: "programa", placeholder: "Matemática"},
    {label: "NÍVEL", nome: "nivel", tipo: "select", opcoes: ["", "Mestrado", "Doutorado"], placeholder: "Selecione o nível"},
    {label: "TIPO DE AUXÍLIO", nome: "tipo_auxilio", tipo: "select", opcoes: ["", "Participação em evento", "Banca de exame ou defesa", "Outro"], placeholder: "Selecione o tipo"},
    {label: "E-MAIL", nome: "email", placeholder: "maria@usp.br"},
    {label: "NOME DO EVENTO / BANCA DE EXAME OU DEFESA", nome: "nome_evento", placeholder: "Nome do evento"},
    {label: "PERÍODO DO EVENTO, EXAME OU DEFESA", nome: "periodo", placeholder: "dd/mm/yyyy a dd/mm/yyyy"},
    {label: "CIDADE DO EVENTO, EXAME OU DEFESA", nome: "cidade_evento", placeholder: "São Paulo"},
    {label: "ESTADO DO EVENTO, EXAME OU DEFESA", nome: "estado_evento", placeholder: "SP"},
    {label: "PAÍS DO EVENTO, EXAME OU DEFESA", nome: "pais_evento", placeholder: "Brasil"},
    {label: "LINK DO EVENTO, EXAME OU DEFESA", nome: "link_evento", placeholder: "https://evento.com", opcional: true},
    {label: "VALOR SOLICITADO (R$)", nome: "valor", placeholder: "1500"},
    {label: "DETALHAMENTO DO PEDIDO", nome: "detalhamento", tipo: "textarea", placeholder: "Detalhe o pedido", opcional: false},
    {label: "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", nome: "apresentacao", tipo: "select", opcoes: ["", "Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"], placeholder: "Selecione o tipo"},
    {label: "ENDEREÇO DO SOLICITANTE", bloco: true},
    {label: "DATA DE NASCIMENTO", nome: "data_nascimento", placeholder: "dd/mm/aaaa"},
    {label: "LOGRADOURO", nome: "logradouro", placeholder: "Rua Exemplo"},
    {label: "NÚMERO", nome: "numero", placeholder: "100"},
    {label: "COMPLEMENTO", nome: "complemento", placeholder: "Apto 12", opcional: true},
    {label: "BAIRRO", nome: "bairro", placeholder: "Centro"},
    {label: "CEP", nome: "cep", placeholder: "00000-000"},
    {label: "CIDADE", nome: "cidade", placeholder: "São Paulo"},
    {label: "ESTADO", nome: "estado", placeholder: "SP"},
    {label: "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO", bloco: true},
    {label: "CPF (SEPARADOS POR PONTOS E TRAÇO)", nome: "cpf", placeholder: "000.000.000-00"},
    {label: "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", nome: "rg", placeholder: "00.000.000-0"},
    {label: "NOME DO BANCO", nome: "banco", placeholder: "Banco do Brasil"},
    {label: "NÚMERO DA AGÊNCIA", nome: "agencia", placeholder: "1234"},
    {label: "NÚMERO DA CONTA", nome: "conta", placeholder: "12345-6"}
];

const camposDocentes = camposAlunos.filter(c => c.nome !== "nivel" && c.nome !== "tipo_auxilio");

function renderForm() {
    const formAlunos = document.getElementById("form-alunos");
    const formDocentes = document.getElementById("form-docentes");
    
    renderCampos(formAlunos, camposAlunos);
    renderCampos(formDocentes, camposDocentes);
}

function renderCampos(form, campos) {
    let blocoDiv = null;
    let camposDiv = null;

    campos.forEach(c => {
        if (c.bloco) {
            if (blocoDiv) form.appendChild(blocoDiv);
            blocoDiv = document.createElement("div");
            blocoDiv.className = "bloco";
            blocoDiv.innerHTML = `<h3>${c.label}</h3>`;
            camposDiv = document.createElement("div");
            camposDiv.className = "campos";
            blocoDiv.appendChild(camposDiv);
        } else if (camposDiv) {
            const div = document.createElement("div");
            div.className = "campo";
            let inputHtml = "";
            if (c.tipo === "select") {
                inputHtml = `<select name="${c.nome}" required ${c.opcional ? "" : "required"} aria-label="${c.label}">`;
                inputHtml += `<option value="" disabled selected hidden>${c.placeholder}</option>`;
                c.opcoes.slice(1).forEach(op => {
                    inputHtml += `<option value="${op}">${op}</option>`;
                });
                inputHtml += `</select>`;
            } else if (c.tipo === "textarea") {
                inputHtml = `<textarea name="${c.nome}" required ${c.opcional ? "" : "required"} placeholder="${c.placeholder}" aria-label="${c.label}"></textarea>`;
            } else {
                inputHtml = `<input type="text" name="${c.nome}" placeholder="${c.placeholder}" aria-label="${c.label}">`;
            }
            div.innerHTML = `<label>${c.label}</label>${inputHtml}`;
            camposDiv.appendChild(div);
        }
    });
    if (blocoDiv) form.appendChild(blocoDiv);
}

function trocarAba(aba) {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    
    document.getElementById(`tab-${aba}`).classList.add("active");
    document.getElementById(`aba-${aba}`).classList.add("active");
}

function formatarMoeda(element) {
    let valor = element.value.replace(/\D/g, "");
    if (valor !== "") {
        valor = parseInt(valor, 10);
        let centavos = valor % 100;
        valor = Math.floor(valor / 100);
        let texto = valor.toLocaleString("pt-BR");
        element.value = `R$ ${texto},${centavos.toString().padStart(2, "0")}`;
    } else {
        element.value = "";
    }
}

function formatarCPF(element) {
    let valor = element.value.replace(/\D/g, "");
    valor = valor.substring(0, 11);
    let formatado = "";
    for (let i = 0; i < valor.length; i++) {
        if (i === 3 || i === 6) formatado += ".";
        if (i === 9) formatado += "-";
        formatado += valor[i];
    }
    element.value = formatado;
}

function formatarCEP(element) {
    let valor = element.value.replace(/\D/g, "");
    valor = valor.substring(0, 8);
    let formatado = valor.substring(0, 5);
    if (valor.length > 5) formatado += "-" + valor.substring(5);
    element.value = formatado;
}

function formatarData(element) {
    let valor = element.value.replace(/\D/g, "");
    valor = valor.substring(0, 8);
    let formatado = valor.substring(0, 2);
    if (valor.length > 2) formatado += "/" + valor.substring(2, 4);
    if (valor.length > 4) formatado += "/" + valor.substring(4, 8);
    element.value = formatado;
}

document.addEventListener("change", e => {
    if (e.target.name === "valor") formatarMoeda(e.target);
    if (e.target.name === "cpf") formatarCPF(e.target);
    if (e.target.name === "cep") formatarCEP(e.target);
    if (e.target.name === "data_nascimento") formatarData(e.target);
});

async function enviarSolicitacao(event, aba) {
    event.preventDefault();
    
    const formId = aba === "alunos" ? "form-alunos" : "form-docentes";
    const errosId = aba === "alunos" ? "erros-alunos" : "erros-docentes";
    
    const form = document.getElementById(formId);
    const formData = new FormData(form);
    const dados = Object.fromEntries(formData.entries());

    const resp = await fetch("/solicitacao", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({aba, dados})
    });

    const body = await resp.json();
    
    if (body.erros) {
        const errosDiv = document.getElementById(errosId);
        errosDiv.innerHTML = body.erros.map(e => `<p>${e}</p>`).join("");
        errosDiv.scrollIntoView({behavior: "smooth", block: "start"});
    } else if (body.oficio) {
        document.querySelectorAll(".tab, .tab-content").forEach(el => el.style.display = "none");
        document.getElementById("confirmacao").style.display = "block";
        document.getElementById("texto-oficio").textContent = body.oficio;
    }
}

function voltarFormulario() {
    document.querySelectorAll(".tab, .tab-content").forEach(el => el.style.display = "");
    document.getElementById("confirmacao").style.display = "none";
    document.querySelectorAll(".erros").forEach(el => el.innerHTML = "");
    document.getElementById("form-alunos").reset();
    document.getElementById("form-docentes").reset();
}

renderForm();
