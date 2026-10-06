document.addEventListener('DOMContentLoaded', () => {
    // Formatting Functions
    const formatarValor = (input) => {
        // Remove tudo que não for dígito
        let digits = input.value.replace(/\D/g, '');
        if (!digits) {
            input.value = '';
            return;
        }
        // Converter para centavos inteiros
        let cents = parseInt(digits, 10);
        if (isNaN(cents)) cents = 0;
        
        // Formatar para BRL
        // Ex: 1500 -> 15,00
        // 150000 -> 1.500,00
        let val = cents / 100;
        let formatted = new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(val);
        
        // Armazenar o valor puro em dataset ou input value? 
        // O requisito diz "os dígitos digitados são os centavos" e "campo passa a mostrar". 
        // Então o input value muda para string formatada, mas para enviar para o backend, 
        // o backend espera a string numérica? Ou espera formatada? 
        // No backend, fiz `formatar_valor` que assume entrada numérica (centavos). 
        // Se o input mostra "R$ 1.500,00", e o JS envia isso, o backend vai quebrar se não tratar.
        // Vou guardar os dígitos originais em um atributo data-* e enviar isso.
        input.dataset.raw = cents;
        input.value = formatted;
    };

    const formatarCPF = (input) => {
        let digits = input.value.replace(/\D/g, '');
        digits = digits.substring(0, 11);
        let formatted = digits;
        if (digits.length > 9) {
            formatted = digits.substring(0, 3) + '.' + digits.substring(3, 6) + '.' + digits.substring(6, 9) + '-' + digits.substring(9, 11);
        } else if (digits.length > 6) {
            formatted = digits.substring(0, 3) + '.' + digits.substring(3, 6) + '.' + digits.substring(6, 9);
        } else if (digits.length > 3) {
            formatted = digits.substring(0, 3) + '.' + digits.substring(3, 6);
        }
        input.value = formatted;
    };

    const formatarCEP = (input) => {
        let digits = input.value.replace(/\D/g, '');
        digits = digits.substring(0, 8);
        if (digits.length > 5) {
            input.value = digits.substring(0, 5) + '-' + digits.substring(5, 8);
        } else {
            input.value = digits;
        }
    };

    const formatarData = (input) => {
        let digits = input.value.replace(/\D/g, '');
        digits = digits.substring(0, 8);
        let formatted = '';
        if (digits.length > 4) {
            formatted = digits.substring(0, 2) + '/' + digits.substring(2, 4) + '/' + digits.substring(4, 8);
        } else if (digits.length > 2) {
            formatted = digits.substring(0, 2) + '/' + digits.substring(2, 4);
        } else {
            formatted = digits;
        }
        input.value = formatted;
    };

    const formatarAgencia = (input) => {
        input.value = input.value.replace(/\D/g, '');
    };

    const formatarNumUSP = (input) => {
        input.value = input.value.replace(/\D/g, '');
    };

    // Attach listeners to all inputs with names specific to formatting
    document.querySelectorAll('input[name="valor_solicitado"]').forEach(input => {
        input.addEventListener('blur', (e) => formatarValor(e.target));
    });
    document.querySelectorAll('input[name="cpf"]').forEach(input => {
        input.addEventListener('blur', (e) => formatarCPF(e.target));
    });
    document.querySelectorAll('input[name="cep"]').forEach(input => {
        input.addEventListener('blur', (e) => formatarCEP(e.target));
    });
    document.querySelectorAll('input[name="data_nascimento"]').forEach(input => {
        input.addEventListener('blur', (e) => formatarData(e.target));
    });
    document.querySelectorAll('input[name="numero_agencia"]').forEach(input => {
        input.addEventListener('blur', (e) => formatarAgencia(e.target));
    });
    document.querySelectorAll('input[name="numusp"]').forEach(input => {
        input.addEventListener('blur', (e) => formatarNumUSP(e.target));
    });

    // Tab logic
    window.openTab = (evt, tabId) => {
        // Hide all tab contents
        let tabcontents = document.querySelectorAll('.tab-content');
        tabcontents.forEach(tc => tc.style.display = 'none');

        // Remove active class from all buttons
        let tablinks = document.querySelectorAll('.tab');
        tablinks.forEach(tl => tl.classList.remove('active'));

        // Show current tab and set active
        document.getElementById(tabId).style.display = 'block';
        evt.currentTarget.classList.add('active');
    };

    // Submit logic
    const handleSubmit = async (event) => {
        event.preventDefault();
        
        const form = event.target;
        const aba = form.id.replace('form-', ''); // 'alunos' ou 'docentes'
        
        // Coletar dados
        const formData = new FormData(form);
        const dados = {};
        
        for (let [key, value] of formData.entries()) {
            // Se for valor solicitado, pegar o dataset.raw se existir, senão o value formatado limpo
            if (key === 'valor_solicitado') {
                const input = form.querySelector('input[name="valor_solicitado"]');
                dados[key] = input.dataset.raw || input.value.replace(/\D/g, '') || '0';
            } else {
                dados[key] = value.trim();
            }
        }
        dados.aba = aba;
        
        // Send to backend
        try {
            const response = await fetch('/solicitacao', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(dados)
            });
            
            const result = await response.json();
            
            const errorList = document.getElementById(`errors-${aba}`);
            errorList.innerHTML = '';
            
            if (result.valido) {
                // Show confirmation
                document.getElementById('form-area').classList.add('show-feedback');
                const feedbackDiv = document.getElementById('feedback');
                const oficioPre = document.getElementById('oficio-texto');
                oficioPre.textContent = result.oficio;
            } else {
                // Show errors
                if (result.erros.length > 0) {
                    result.erros.forEach(erro => {
                        const li = document.createElement('li');
                        li.textContent = erro;
                        errorList.appendChild(li);
                    });
                    errorList.style.display = 'block';
                } else {
                    errorList.style.display = 'none';
                }
            }
        } catch (err) {
            console.error(err);
            alert('Erro ao enviar solicitação');
        }
    };

    document.getElementById('form-alunos').addEventListener('submit', handleSubmit);
    document.getElementById('form-docentes').addEventListener('submit', handleSubmit);
});