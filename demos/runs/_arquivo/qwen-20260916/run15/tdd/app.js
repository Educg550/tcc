document.addEventListener('DOMContentLoaded', () => {
    // Tabs
    const tabs = document.querySelectorAll('.tab-btn');
    const forms = document.querySelectorAll('.tab-content');
    const formSection = document.getElementById('form-section');
    const oficioSection = document.getElementById('oficio-section');
    const errosContainer = document.getElementById('erros-container');
    const oficioText = document.getElementById('oficio-text');
    const btnNovaSolicitacao = document.getElementById('btn-nova-solicitacao');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.getAttribute('data-tab');
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            forms.forEach(f => {
                if(f.getAttribute('data-tab-form') === targetTab) {
                    f.classList.add('active');
                    f.style.display = 'block';
                } else {
                    f.classList.remove('active');
                    f.style.display = 'none';
                }
            });
            errosContainer.style.display = 'none';
            errosContainer.innerHTML = '';
        });
    });

    // Formatting Functions
    function formatValue(input) {
        const digits = input.value.replace(/\D/g, '');
        if (!digits) return '';
        const cents = parseInt(digits, 10);
        return 'R$ ' + cents.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function formatCPF(input) {
        const digits = input.value.replace(/\D/g, '');
        const max = digits.slice(0, 3);
        if (max.length === 3) {
            const mid = digits.slice(3, 6);
            if (mid.length === 3) {
                const rest = digits.slice(6, 9);
                if (rest.length === 3) {
                    const check = digits.slice(9, 11);
                    return `${max}.${mid}.${rest}-${check}`;
                }
                return `${max}.${mid}.${rest}`;
            }
            return `${max}.${mid}`;
        }
        return max;
    }

    function formatCEP(input) {
        const digits = input.value.replace(/\D/g, '');
        if (digits.length === 8) {
            const first = digits.slice(0, 5);
            const last = digits.slice(5, 8);
            return `${first}-${last}`;
        }
        return digits;
    }

    function formatDate(input) {
        const digits = input.value.replace(/\D/g, '');
        const day = digits.slice(0, 2);
        if (day.length === 2) {
            const month = digits.slice(2, 4);
            if (month.length === 2) {
                const year = digits.slice(4, 8);
                return `${day}/${month}/${year}`;
            }
            return `${day}/${month}`;
        }
        return day;
    }

    // Attach Blur events for formatting
    document.querySelectorAll('input[name="valor"]').forEach(el => {
        el.addEventListener('blur', () => el.value = formatValue(el));
    });
    document.querySelectorAll('input[name="cpf"]').forEach(el => {
        el.addEventListener('blur', () => el.value = formatCPF(el));
    });
    document.querySelectorAll('input[name="cep"]').forEach(el => {
        el.addEventListener('blur', () => el.value = formatCEP(el));
    });
    document.querySelectorAll('input[name="data_nascimento"]').forEach(el => {
        el.addEventListener('blur', () => el.value = formatDate(el));
    });

    // Submit Handlers
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const payload = Object.fromEntries(formData.entries());
            payload.aba = form.getAttribute('data-tab-form');

            // For ALUNOS level/type and DOCENTES, ensure empty selects are sent as empty string or handled by backend logic if necessary.
            // The backend validation tests expect strings. 
            if (payload.aba === 'docentes') {
                payload.tipo_auxilio = '';
                payload.nivel = '';
            }

            try {
                const response = await fetch('/solicitacao', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await response.json();

                if (result.oficio) {
                    formSection.style.display = 'none';
                    oficioText.textContent = result.oficio;
                    oficioSection.style.display = 'block';
                } else {
                    // Display errors
                    errosContainer.innerHTML = '';
                    if(result.erros) {
                        result.erros.forEach(erro => {
                            const p = document.createElement('p');
                            p.textContent = erro;
                            errosContainer.appendChild(p);
                        });
                    }
                    errosContainer.style.display = 'block';
                    window.scrollTo(0, 0);
                }
            } catch (err) {
                console.error(err);
            }
        });
    });

    btnNovaSolicitacao.addEventListener('click', () => {
        oficioSection.style.display = 'none';
        formSection.style.display = 'block';
        document.querySelectorAll('form').forEach(f => f.reset());
        errosContainer.style.display = 'none';
    });
});