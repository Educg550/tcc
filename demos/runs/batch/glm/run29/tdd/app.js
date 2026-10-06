// JavaScript do formulário de solicitação de auxílio financeiro - Pós-Graduação IME-USP

// Função para alternar entre as abas ALUNOS e DOCENTES
function switchTab(tabName) {
    // Remove a classe active da aba atual e adiciona na nova
    document.querySelectorAll(".tab").forEach(function(t) {
        t.classList.remove("active");
    });
    
    // Esconde todos os conteúdos de aba
    document.querySelectorAll(".tab-content").forEach(function(c) {
        c.classList.add("hidden");
    });
    
    // Mostra a aba selecionada
    if (tabName === "alunos") {
        document.getElementById("tab-alunos").classList.add("active");
        document.getElementById("tab-content-alunos").classList.remove("hidden");
    } else if (tabName === "docentes") {
        document.getElementById("tab-docentes").classList.add("active");
        document.getElementById("tab-content-docentes").classList.remove("hidden");
    }
}

// Função para formatar o valor em moeda brasileira
function formatarValor(inputId) {
    var input = document.getElementById(inputId);
    var digits = input.value.replace(/\D/g, "");
    if (digits === "") {
        return;
    }
    
    // Os dígitos digitados são os centavos do valor
    var centavos = parseInt(digits, 10);
    var reais = Math.floor(centavos / 100);
    var cent = centavos % 100;
    
    // Formata com separador de milhar
    var reaisStr = reais.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    
    input.value = "R$ " + reaisStr + "," + (cent < 10 ? "0" : "") + cent;
}

// Função para formatar CPF (000.000.000-00)
function formatarCpf(inputId) {
    var input = document.getElementById(inputId);
    var digits = input.value.replace(/\D/g, "");
    if (digits === "") {
        return;
    }
    
    digits = digits.substring(0, 11);
    
    var cpf = "";
    if (digits.length <= 3) {
        cpf = digits;
    } else if (digits.length <= 6) {
        cpf = digits.substring(0, 3) + "." + digits.substring(3);
    } else if (digits.length <= 9) {
        cpf = digits.substring(0, 3) + "." + digits.substring(3, 6) + "." + digits.substring(6);
    } else {
        cpf = digits.substring(0, 3) + "." + digits.substring(3, 6) + "." + digits.substring(6, 9) + "-" + digits.substring(9);
    }
    
    input.value = cpf;
}

// Função para formatar CEP (00000-000)
function formatarCep(inputId) {
    var input = document.getElementById(inputId);
    var digits = input.value.replace(/\D/g, "");
    if (digits === "") {
        return;
    }
    
    digits = digits.substring(0, 8);
    
    if (digits.length <= 5) {
        input.value = digits;
    } else {
        input.value = digits.substring(0, 5) + "-" + digits.substring(5);
    }
}

// Função para formatar Data de Nascimento (dd/mm/aaaa)
function formatarData(inputId) {
    var input = document.getElementById(inputId);
    var digits = input.value.replace(/\D/g, "");
    if (digits === "") {
        return;
    }
    
    digits = digits.substring(0, 8);
    
    var data = "";
    if (digits.length <= 2) {
        data = digits;
    } else if (digits.length <= 4) {
        data = digits.substring(0, 2) + "/" + digits.substring(2);
    } else {
        data = digits.substring(0, 2) + "/" + digits.substring(2, 4) + "/" + digits.substring(4);
    }
    
    input.value = data;
}

// Função para enviar o formulário via fetch
function submitForm(event, tipo) {
    event.preventDefault();
    
    var form = event.target;
    var formData = new FormData(form);
    formData.append("tipo", tipo);
    
    fetch("/solicitar", {
        method: "POST",
        body: formData
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        if (data.ok) {
            // Mostra a confirmação e o ofício
            document.getElementById("tabs-container").classList.add("hidden");
            document.getElementById("confirmation").classList.remove("hidden");
            document.getElementById("oficio").textContent = data.oficio;
        } else {
            // Mostra as mensagens de erro
            var errorDiv = document.getElementById("error-message-" + tipo);
            errorDiv.innerHTML = "";
            
            data.erros.forEach(function(erro) {
                var p = document.createElement("p");
                p.textContent = erro;
                errorDiv.appendChild(p);
            });
            
            errorDiv.classList.add("show");
        }
    })
    .catch(function(error) {
        console.error("Erro ao enviar formulário:", error);
    });
}
