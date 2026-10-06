document.addEventListener('DOMContentLoaded', () => {
    // Tab Switching
    const tabs = document.querySelectorAll('.tab-button');
    const forms = document.querySelectorAll('.form-content');
    const errorsContainer = document.getElementById('errors-container');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-tab');
            
            // Update Tab Buttons
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Show/Hide Forms
            forms.forEach(f => {
                if(f.getAttribute('data-aba') === target) {
                    f.classList.add('active');
                } else {
                    f.classList.remove('active');
                }
            });
            
            // Clear errors on tab switch
            errorsContainer.style.display = 'none';
            errorsContainer.innerHTML = '';
        });
    });

    // Formatters
    const formatCurrency = (value) => {
        const digits = value.replace(/\D/g, '');
        if (!digits) return '';
        const num = parseInt(digits, 10) / 100;
        return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    };

    const formatCPF = (value) => {
        value = value.replace(/\D/g, '');
        if (value.length > 11) value = value.substring(0, 11);
        
        if (value.length > 9) {
            value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, '$1.$2.$3-$4');
        } else if (value.length > 6) {
            value = value.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
        } else if (value.length > 3) {
            value = value.replace(/(\d{3})(\d{1,3})/, '$1.$2');
        }
        return value;
    };

    const formatCEP = (value) => {
        value = value.replace(/\D/g, '');
        if (value.length > 8) value = value.substring(0, 8);
        if (value.length > 5) {
            value = value.substring(0, 5) + '-' + value.substring(5);
        }
        return value;
    };

    const formatDate = (value) => {
        value = value.replace(/\D/g, '');
        if (value.length > 8) value = value.substring(0, 8);
        if (value.length > 4) {
            value = value.substring(0, 2) + '/' + value.substring(2, 4) + '/' + value.substring(4);
        } else if (value.length > 2) {
            value = value.substring(0, 2) + '/' + value.substring(2);
        }
        return value;
    };

    // Attach Blur Listeners to Formatters
    document.querySelectorAll('.format-currency').forEach(input => {
        input.addEventListener('blur', (e) => {
            e.target.value = formatCurrency(e.target.value);
        });
    });

    document.querySelectorAll('.format-cpf').forEach(input => {
        input.addEventListener('blur', (e) => {
            e.target.value = formatCPF(e.target.value);
        });
    });

    document.querySelectorAll('.format-cep').forEach(input => {
        input.addEventListener('blur', (e) => {
            e.target.value = formatCEP(e.target.value);
        });
    });

    document.querySelectorAll('.format-date').forEach(input => {
        input.addEventListener('blur', (e) => {
            e.target.value = formatDate(e.target.value);
        });
    });

    // Form Submission
    forms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const aba = form.getAttribute('data-aba');
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            data.aba = aba;

            try {
                const response = await fetch('/api/solicitar', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data),
                });

                const result = await response.json();

                if (result.erros && result.erros.length > 0) {
                    // Show Errors
                    let errHtml = '<ul>';
                    result.erros.forEach(err => {
                        errHtml += `<li>${err}</li>`;
                    });
                    errHtml += '</ul>';
                    errorsContainer.innerHTML = errHtml;
                    errorsContainer.style.display = 'block';
                    errorsContainer.scrollIntoView({ behavior: 'smooth' });
                } else if (result.oficio) {
                    // Show Confirmation
                    const formContainer = document.getElementById('form-container');
                    const confContainer = document.getElementById('confirmation-container');
                    const oficioContent = document.getElementById('oficio-content');
                    
                    oficioContent.textContent = Array.isArray(result.oficio) ? result.oficio.join('\n') : result.oficio;
                    
                    formContainer.classList.add('hidden');
                    confContainer.classList.remove('hidden');
                }
            } catch (error) {
                console.error('Error submitting form:', error);
                alert('Ocorreu um erro ao enviar a solicitação.');
            }
        });
    });

    // Back Button
    const backBtn = document.getElementById('back-btn');
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            document.getElementById('confirmation-container').classList.add('hidden');
            document.getElementById('form-container').classList.remove('hidden');
        });
    }
});