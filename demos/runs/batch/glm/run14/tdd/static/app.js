// Troca entre as abas ALUNOS e DOCENTES
function trocarAba(aba) {
    document.getElementById('form-alunos').classList.toggle('hidden', aba !== 'alunos');
    document.getElementById('form-docentes').classList.toggle('hidden', aba !== 'docentes');
    document.getElementById('tab-alunos').classList.toggle('active', aba === 'alunos');
    document.getElementById('tab-docentes').classList.toggle('active', aba === 'docentes');
}

// Funções de formatação de campos (chamadas no onblur)
function formatarValor(campo) {
    const digitos = campo.value.replace(/\D/g, '');
    if (!digitos) { campo.value = ''; return; }
    const centavos = parseInt(digitos, 10);
    const reais = Math.floor(centavos / 100);
    const cent = centavos % 100;
    campo.value = 'R$ ' + reais.toLocaleString('pt-BR') + ',' + String(cent).padStart(2, '0');
}

function formatarCpf(campo) {
    const d = campo.value.replace(/\D/g, '').slice(0, 11);
    if (d.length === 11) {
        campo.value = d.slice(0,3) + '.' + d.slice(3,6) + '.' + d.slice(6,9) + '-' + d.slice(9);
    }
}

function formatarCep(campo) {
    const d = campo.value.replace(/\D/g, '').slice(0, 8);
    if (d.length === 8) {
        campo.value = d.slice(0,5) + '-' + d.slice(5);
    }
}

function formatarData(campo) {
    const d = campo.value.replace(/\D/g, '').slice(0, 8);
    if (d.length === 8) {
        campo.value = d.slice(0,2) + '/' + d.slice(2,4) + '/' + d.slice(4);
    }
}

// Mostra a lista de erros no topo do formulário da aba ativa
function mostrarErros(tipo, erros) {
    const div = document.getElementById('erros-' + tipo);
    div.style.display = erros.length ? 'block' : 'none';
    div.innerHTML = erros.length
        ? '<ul>' + erros.map(e => '<li>' + e + '</li>').join('') + '</ul>'
        : '';
}

// Envio do formulário para a API
async function enviar(event, tipo) {
    event.preventDefault();
    const form = document.getElementById(tipo === 'alunos' ? 'formAlunos' : 'formDocentes');
    const dados = Object.fromEntries(new FormData(form).entries());
    dados.tipo = tipo;

    try {
        const resposta = await fetch('/api/solicitacao', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados),
        });
        const resultado = await resposta.json();

        if (resultado.erros && resultado.erros.length > 0) {
            mostrarErros(tipo, resultado.erros);
            return false;
        }

        // Sucesso: esconde formulários e mostra o ofício
        document.getElementById('form-alunos').classList.add('hidden');
        document.getElementById('form-docentes').classList.add('hidden');
        document.querySelector('.tabs').classList.add('hidden');
        document.getElementById('oficio').textContent = resultado.oficio;
        document.getElementById('confirmacao').classList.remove('hidden');
        window.scrollTo(0, 0);
    } catch (erro) {
        mostrarErros(tipo, ['Erro de comunicação com o servidor. Tente novamente.']);
    }
    return false;
}
