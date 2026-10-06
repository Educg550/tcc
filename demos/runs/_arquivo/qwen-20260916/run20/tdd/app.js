document.addEventListener("DOMContentLoaded", () => {
    const tabButtons = document.querySelectorAll(".tab-button");
    const forms = document.querySelectorAll(".tab-content");
    const formSection = document.getElementById("form-section");
    const confirmSection = document.getElementById("confirmation-section");
    const errorDiv = document.getElementById("error-messages");

    // Tab switching
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const target = btn.getAttribute("data-target");
            forms.forEach(form => {
                if (form.id === target) {
                    form.classList.add("active");
                } else {
                    form.classList.remove("active");
                }
            });
            errorDiv.style.display = "none";
            errorDiv.innerHTML = "";
        });
    });

    // Formatting functions
    const formatCPF = (value) => {
        value = value.replace(/\D/g, '');
        if (value.length > 11) value = value.slice(0, 11);
        value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{2}).*/, '$1.$2.$3-$4');
        value = value.replace(/(\d{3})(\d{3})(\d{3})/, '$1.$2.$3');
        return value;
    };

    const formatCEP = (value) => {
        value = value.replace(/\D/g, '');
        if (value.length > 8) value = value.slice(0, 8);
        return value.replace(/(\d{5})(\d{3})/, '$1-$2');
    };

    const formatDate = (value) => {
        value = value.replace(/\D/g, '');
        if (value.length > 8) value = value.slice(0, 8);
        return value.replace(/(\d{2})(\d{2})(\d{4})/, '$1/$2/$3');
    };

    const formatMoneyInput = (value) => {
        value = value.replace(/\D/g, '');
        if (value === '') return '';
        let num = BigInt(value);
        let formatted = num.toString();
        if (formatted.length <= 2) {
            formatted = '0'.repeat(3 - formatted.length) + formatted;
        } else {
            formatted = formatted.slice(0, -2) + '.' + formatted.slice(-2);
        }
        let parts = formatted.split('.');
        let intPart = parts[0];
        let decPart = parts[1];
        intPart = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        return `R$ ${intPart},${decPart}`;
    };

    // Bind blur events for formatting
    document.querySelectorAll('input[name="cpf"]').forEach(input => {
        input.addEventListener('blur', (e) => {
            e.target.value = formatCPF(e.target.value);
        });
    });

    document.querySelectorAll('input[name="cep"]').forEach(input => {
        input.addEventListener('blur', (e) => {
            e.target.value = formatCEP(e.target.value);
        });
    });

    document.querySelectorAll('input[name="data_nascimento"]').forEach(input => {
        input.addEventListener('blur', (e) => {
            e.target.value = formatDate(e.target.value);
        });
    });

    document.querySelectorAll('input[name="valor"]').forEach(input => {
        input.addEventListener('blur', (e) => {
            e.target.value = formatMoneyInput(e.target.value);
        });
    });

    // Submit handling
    forms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const tipo = form.getAttribute('data-tipo');
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            data.tipo = tipo;

            // Parse valor to integer cents
            const valorCents = data.valor.replace(/\D/g, '');
            data.valor = valorCents ? parseInt(valorCents) : 0;

            // Send to backend
            try {
                const res = await fetch('/solicitar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await res.json();

                if (result.sucesso) {
                    // Show confirmation
                    formSection.classList.add('hidden');
                    confirmSection.classList.remove('hidden');
                    document.getElementById('oficio-text').textContent = result.oficio;
                    window.scrollTo(0,0);
                } else {
                    // Show errors
                    errorDiv.style.display = 'block';
                    errorDiv.innerHTML = '<ul>' + result.erros.map(err => `<li>${err}</li>`).join('') + '</ul>';
                    // Scroll to errors
                    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            } catch (err) {
                alert('Erro ao conectar com o servidor: ' + err.message);
            }
        });
    });
});
