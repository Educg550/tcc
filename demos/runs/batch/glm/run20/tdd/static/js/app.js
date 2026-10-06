document.addEventListener("DOMContentLoaded", () => {
    const botoesAba = document.querySelectorAll(".js-tab-button");
    const paineisAba = document.querySelectorAll(".js-tab-panel");

    botoesAba.forEach((botao) => {
        botao.addEventListener("click", () => {
            const abaAtiva = botao.dataset.tab;

            botoesAba.forEach((b) => {
                b.setAttribute("aria-selected", String(b === botao));
            });

            paineisAba.forEach((painel) => {
                painel.hidden = painel.dataset.tab !== abaAtiva;
            });
        });
    });

    document.querySelectorAll(".js-form").forEach((form) => {
        form.addEventListener("submit", async (evento) => {
            evento.preventDefault();

            const aba = form.id.replace("form-", "");
            const dados = Object.fromEntries(new FormData(form).entries());
            dados["aba"] = aba;

            try {
                const resposta = await fetch("/enviar", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(dados),
                });

                const resultado = await resposta.json();
                const containerMensagens = form.querySelector(".form__messages");

                if (!resultado.ok) {
                    containerMensagens.innerHTML = resultado.erros
                        .map((erro) => `<p>${erro}</p>`)
                        .join("");
                    containerMensagens.hidden = false;
                    return;
                }

                window.location.href = `/confirmacao?oficio=${encodeURIComponent(resultado.oficio)}`;
            } catch (erro) {
                console.error("Erro ao enviar formulário:", erro);
            }
        });
    });

    configurarFormatacaoCampos();
});

function configurarFormatacaoCampos() {
    document.querySelectorAll(".js-form").forEach((form) => {
        form.addEventListener("focusout", (evento) => {
            const campo = evento.target;
            const nome = campo.name;

            if (nome === "valor_solicitado") {
                campo.value = formatarMoeda(campo.value);
            } else if (nome === "cpf") {
                campo.value = formatarCpf(campo.value);
            } else if (nome === "cep") {
                campo.value = formatarCep(campo.value);
            } else if (nome === "data_de_nascimento") {
                campo.value = formatarData(campo.value);
            }
        });
    });
}

function formatarMoeda(valor) {
    const digitos = valor.replace(/\D/g, "");
    if (!digitos) {
        return "";
    }

    const centavos = parseInt(digitos, 10);
    const parteInteira = Math.floor(centavos / 100);
    const resto = centavos % 100;

    const parteInteiraFormatada = parteInteira.toLocaleString("pt-BR");
    return `R$ ${parteInteiraFormatada},${String(resto).padStart(2, "0")}`;
}

function formatarCpf(valor) {
    const digitos = valor.replace(/\D/g, "").slice(0, 11);
    return digitos.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
}

function formatarCep(valor) {
    const digitos = valor.replace(/\D/g, "").slice(0, 8);
    return digitos.replace(/(\d{5})(\d{3})/, "$1-$2");
}

function formatarData(valor) {
    const digitos = valor.replace(/\D/g, "").slice(0, 8);
    return digitos.replace(/(\d{2})(\d{2})(\d{4})/, "$1/$2/$3");
}
