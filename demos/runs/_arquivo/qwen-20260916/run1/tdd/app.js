document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.tab-button');
    const forms = document.querySelectorAll('.form-content');
    const formSection = document.getElementById('form-section');
    const confirmSection = document.getElementById('confirmation-section');
    const oficioText = document.getElementById('oficio-text');
    const errorDisplay = document.getElementById('error-display');

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            tabs.forEach(t => t.classList.remove('active'));
            forms.forEach(f => f.style.display = 'none');
            forms.forEach(f => f.classList.remove('active'));

            this.classList.add('active');
            const target = this.getAttribute('data-tab');
            const form = document.getElementById('form-' + target.toLowerCase());
            form.style.display = 'block';
            form.classList.add('active');
            errorDisplay.textContent = '';
        });
    });

    function formatCpf(value) {
        value = value.replace(/\D/g, '');
        value = value.substring(0, 11);
        let formatted = '';
        for (let i = 0; i < value.length; i++) {
            if (i === 3 || i === 6) formatted += '.';
            if (i === 9) formatted += '-';
            formatted += value[i];
        }
        return formatted;
    }

    function formatCep(value) {
        value = value.replace(/\D/g, '');
        value = value.substring(0, 8);
        return value.length > 5 ? value.slice(0,5) + '-' + value.slice(5) : value;
    }

    function formatDate(value) {
        value = value.replace(/\D/g, '');
        value = value.substring(0, 8);
        let formatted = '';
        for (let i = 0; i < value.length; i++) {
            if (i === 2 || i === 4) formatted += '/';
            formatted += value[i];
        }
        return formatted;
    }

    function formatCurrency(value) {
        value = value.replace(/\D/g, '');
        value = value.replace(/^0+/, '');
        if (value === '') return '';
        const num = parseInt(value, 10) / 100;
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(num);
    }

    const cpfInputs = document.querySelectorAll('.cpf');
    const cepInputs = document.querySelectorAll('.cep');
    const dateInputs = document.querySelectorAll('.data');
    const moedaInputs = document.querySelectorAll('.moeda');

    cpfInputs.forEach(i => i.addEventListener('blur', function() { this.value = formatCpf(this.value); }));
    cepInputs.forEach(i => i.addEventListener('blur', function() { this.value = formatCep(this.value); }));
    dateInputs.forEach(i => i.addEventListener('blur', function() { this.value = formatDate(this.value); }));
    moedaInputs.forEach(i => i.addEventListener('blur', function() { this.value = formatCurrency(this.value); }));

    function handleFormSubmit(form, aba) {
        const formData = new FormData(form);
        const payload = Object.fromEntries(formData.entries());
        payload.aba = aba;

        fetch('/solicitar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(response => {
            return response.json().then(data => ({ status: response.status, body: data }));
        })
        .then(res => {
            if (res.status === 200 && res.body.oficio) {
                errorDisplay.textContent = '';
                oficioText.textContent = res.body.oficio;
                formSection.style.display = 'none';
                confirmSection.style.display = 'block';
            } else if (res.body.erro) {
                errorDisplay.textContent = res.body.erro.join('\n');
            }
        })
        .catch(err => console.error(err));
    }

    document.getElementById('form-alunos').addEventListener('submit', function(e) {
        e.preventDefault();
        handleFormSubmit(this, 'ALUNOS');
    });

    document.getElementById('form-docentes').addEventListener('submit', function(e) {
        e.preventDefault();
        handleFormSubmit(this, 'DOCENTES');
    });
});
