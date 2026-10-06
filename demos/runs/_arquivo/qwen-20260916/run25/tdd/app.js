document.addEventListener('DOMContentLoaded', function() {

    const camposAlunos = [
        { id: 'nome', label: 'NOME COMPLETO - SEM ABREVIAR', type: 'text', bloco: 'SOLICITANTE E EVENTO', placeholder: 'Maria Silva Souza', classe: 'wide6' },
        { id: 'nusp', label: 'N. USP', type: 'text', bloco: 'SOLICITANTE E EVENTO', placeholder: '1234567', classe: 'wide2' },
        { id: 'programa', label: 'PROGRAMA', type: 'text', bloco: 'SOLICITANTE E EVENTO', placeholder: 'Ciência da Computação', classe: 'wide4' },
        { id: 'nivel', label: 'NÍVEL', type: 'select', bloco: 'SOLICITANTE E EVENTO', placeholder: 'Selecione', options: ['Mestrado', 'Doutorado'], classe: 'wide3' },
        { id: 'tipo_auxilio', label: 'TIPO DE AUXÍLIO', type: 'select', bloco: 'SOLICITANTE E EVENTO', placeholder: 'Selecione', options: ['Participação em evento', 'Banca de exame ou defesa', 'Outro'], classe: 'wide3' },
        { id: 'email', label: 'E-MAIL', type: 'email', bloco: 'SOLICITANTE E EVENTO', placeholder: 'maria@ime.usp.br', classe: 'wide3' },
        { id: 'evento', label: 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', type: 'text', bloco: 'SOLICITANTE E EVENTO', placeholder: 'XVII SBC', classe: 'wide3' },
        { id: 'periodo', label: 'PERÍODO DO EVENTO, EXAME OU DEFESA', type: 'text', bloco: 'SOLICITANTE E EVENTO', placeholder: '10 a 14 de julho de 2025', classe: 'wide3' },
        { id: 'cidade_evento', label: 'CIDADE DO EVENTO, EXAME OU DEFESA', type: 'text', bloco: 'SOLICITANTE E EVENTO', placeholder: 'Belo Horizonte', classe: 'wide2' },
        { id: 'estado_evento', label: 'ESTADO DO EVENTO, EXAME OU DEFESA', type: 'text', bloco: 'SOLICITANTE E EVENTO', placeholder: 'MG', classe: 'wide1' },
        { id: 'pais_evento', label: 'PAÍS DO EVENTO, EXAME OU DEFESA', type: 'text', bloco: 'SOLICITANTE E EVENTO', placeholder: 'Brasil', classe: 'wide1' },
        { id: 'link', label: 'LINK DO EVENTO, EXAME OU DEFESA', type: 'text', bloco: 'SOLICITANTE E EVENTO', placeholder: 'https://sbc.org.br', classe: 'wide2' },
        { id: 'valor', label: 'VALOR SOLICITADO (R$)', type: 'text', bloco: 'SOLICITANTE E EVENTO', placeholder: '1500 (centavos)', classe: 'wide3' },
        { id: 'detalhamento', label: 'DETALHAMENTO DO PEDIDO', type: 'textarea', bloco: 'SOLICITANTE E EVENTO', placeholder: 'Detalhes do pedido...', classe: 'wide6' },
        { id: 'apresentacao', label: 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', type: 'select', bloco: 'SOLICITANTE E EVENTO', placeholder: 'Selecione', options: ['Pôster', 'Apresentação oral', 'Outra', 'Não irá apresentar trabalho'], classe: 'wide3' },
        { id: 'nascimento', label: 'DATA DE NASCIMENTO', type: 'text', bloco: 'ENDEREÇO DO SOLICITANTE', placeholder: 'dd/mm/aaaa', classe: 'wide2' },
        { id: 'logradouro', label: 'LOGRADOURO', type: 'text', bloco: 'ENDEREÇO DO SOLICITANTE', placeholder: 'Rua do Matão', classe: 'wide2' },
        { id: 'numero', label: 'NÚMERO', type: 'text', bloco: 'ENDEREÇO DO SOLICITANTE', placeholder: '1010', classe: 'wide1' },
        { id: 'complemento', label: 'COMPLEMENTO', type: 'text', bloco: 'ENDEREÇO DO SOLICITANTE', placeholder: 'Bloco C', classe: 'wide2' },
        { id: 'bairro', label: 'BAIRRO', type: 'text', bloco: 'ENDEREÇO DO SOLICITANTE', placeholder: 'Cidade Universitária', classe: 'wide2' },
        { id: 'cep', label: 'CEP', type: 'text', bloco: 'ENDEREÇO DO SOLICITANTE', placeholder: '05508-090', classe: 'wide2' },
        { id: 'cidade', label: 'CIDADE', type: 'text', bloco: 'ENDEREÇO DO SOLICITANTE', placeholder: 'São Paulo', classe: 'wide2' },
        { id: 'estado', label: 'ESTADO', type: 'text', bloco: 'ENDEREÇO DO SOLICITANTE', placeholder: 'SP', classe: 'wide1' },
        { id: 'cpf', label: 'CPF (SEPARADOS POR PONTOS E TRAÇO)', type: 'text', bloco: 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO', placeholder: '000.000.000-00', classe: 'wide2' },
        { id: 'rg', label: 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', type: 'text', bloco: 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO', placeholder: '12.345.678-9', classe: 'wide2' },
        { id: 'banco', label: 'NOME DO BANCO', type: 'text', bloco: 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO', placeholder: 'Banco do Brasil', classe: 'wide2' },
        { id: 'agencia', label: 'NÚMERO DA AGÊNCIA', type: 'text', bloco: 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO', placeholder: '1234', classe: 'wide1' },
        { id: 'conta', label: 'NÚMERO DA CONTA', type: 'text', bloco: 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO', placeholder: '56789-0', classe: 'wide1' },
    ];

    const blocos = ['SOLICITANTE E EVENTO', 'ENDEREÇO DO SOLICITANTE', 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO'];
    
    function renderizarFormulario(targetId, campos) {
        const target = document.getElementById(targetId);
        let html = '';
        
        blocos.forEach(blocoNome => {
            const camposDoBloco = campos.filter(c => c.bloco === blocoNome);
            if (camposDoBloco.length > 0) {
                html += `<div class="bloco"><h3>${blocoNome}</h3><div class="grid">`;
                camposDoBloco.forEach(campo => {
                    if (campo.type === 'select') {
                        let optionsHtml = '<option value="">' + (campo.placeholder || 'Selecione') + '</option>';
                        campo.options.forEach(opt => {
                            optionsHtml += `<option value="${opt}">${opt}</option>`;
                        });
                        html += `<div class="grupo ${campo.classe}"><label>${campo.label}</label><select id="al-${campo.id}" name="${campo.id}">${optionsHtml}</select></div>`;
                    } else if (campo.type === 'textarea') {
                        html += `<div class="grupo ${campo.classe}"><label>${campo.label}</label><textarea id="al-${campo.id}" name="${campo.id}" placeholder="${campo.placeholder}"></textarea></div>`;
                    } else {
                        html += `<div class="grupo ${campo.classe}"><label>${campo.label}</label><input type="${campo.type}" id="al-${campo.id}" name="${campo.id}" placeholder="${campo.placeholder}"></div>`;
                    }
                });
                html += `</div></div>`;
            }
        });
        
        target.innerHTML = html;
        
        // Bind blur formatters
        document.getElementById('al-valor').addEventListener('blur', function(e) {
            e.target.value = formatarValor(e.target.value);
        });
        document.getElementById('al-cep').addEventListener('blur', function(e) {
            e.target.value = formatarCep(e.target.value);
        });
        document.getElementById('al-nascimento').addEventListener('blur', function(e) {
            e.target.value = formatarData(e.target.value);
        });
        document.getElementById('al-cpf').addEventListener('blur', function(e) {
            e.target.value = formatarCpf(e.target.value);
        });
    }

    renderizarFormulario('form-alunos-inner', camposAlunos);
    renderizarFormulario('form-docentes-inner', camposAlunos.filter(c => c.id !== 'nivel' && c.id !== 'tipo_auxilio'));

    // Tabs logic
    const tabAlunos = document.getElementById('tab-alunos');
    const tabDocentes = document.getElementById('tab-docentes');
    const formAlunos = document.getElementById('form-alunos');
    const formDocentes = document.getElementById('form-docentes');
    const formArea = document.getElementById('form-area');
    const confirmArea = document.getElementById('confirm-area');
    const oficioText = document.getElementById('oficio-text');

    tabAlunos.addEventListener('click', () => {
        tabAlunos.classList.add('active');
        tabDocentes.classList.remove('active');
        formAlunos.style.display = 'block';
        formDocentes.style.display = 'none';
    });

    tabDocentes.addEventListener('click', () => {
        tabDocentes.classList.add('active');
        tabAlunos.classList.remove('active');
        formDocentes.style.display = 'block';
        formAlunos.style.display = 'none';
    });

    // Submit logic
    function getFormData(form) {
        const formData = new FormData(form);
        const obj = {};
        for (let [key, value] of formData.entries()) {
            obj[key] = value;
        }
        return obj;
    }

    async function enviarSolicitacao(form) {
        const body = getFormData(form);
        const res = await fetch('/solicitacao', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        const erroBox = document.getElementById('erro-mensagens');
        
        if (data.erros && data.erros.length > 0) {
            erroBox.style.display = 'block';
            erroBox.innerHTML = data.erros.map(e => `<div>${e}</div>`).join('');
        } else {
            erroBox.style.display = 'none';
            formArea.style.display = 'none';
            confirmArea.style.display = 'block';
            oficioText.textContent = data.oficio;
        }
    }

    formAlunos.addEventListener('submit', (e) => { e.preventDefault(); enviarSolicitacao(formAlunos); });
    formDocentes.addEventListener('submit', (e) => { e.preventDefault(); enviarSolicitacao(formDocentes); });

});

function formatarValor(v) {
    let num = String(v).replace(/\D/g, '');
    if (!num) return '';
    let cents = Number(num);
    let reais = Math.floor(cents / 100);
    let centsFormatado = (cents % 100).toString().padStart(2, '0');
    let milhar = reais.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return `R$ ${milhar},${centsFormatado}`;
}

function formatarCpf(v) {
    let num = String(v).replace(/\D/g, '');
    num = num.substring(0, 11);
    num = num.replace(/(\d{3})(\d{0,3})(\d{0,3})(\d{0,2})/, (m, a, b, c, d) => {
        let out = '';
        if (a) out += a + '.';
        if (b) out += b + '.';
        if (c) out += c + '-';
        if (d) out += d;
        return out;
    });
    return num;
}

function formatarCep(v) {
    let num = String(v).replace(/\D/g, '');
    num = num.substring(0, 8);
    if (num.length > 5) {
        return num.substring(0, 5) + '-' + num.substring(5);
    }
    return num;
}

function formatarData(v) {
    let num = String(v).replace(/\D/g, '');
    num = num.substring(0, 8);
    if (num.length > 4) {
        return num.substring(0, 2) + '/' + num.substring(2, 4) + '/' + num.substring(4);
    } else if (num.length > 2) {
        return num.substring(0, 2) + '/' + num.substring(2);
    }
    return num;
}
