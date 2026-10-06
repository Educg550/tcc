document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.tab-btn');
    const forms = {
        'ALUNOS': document.getElementById('form-alunos'),
        'DOCENTES': document.getElementById('form-docentes')
    };

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('ativa'));
            tab.classList.add('ativa');
            Object.values(forms).forEach(f => f.style.display = 'none');
            const target = tab.dataset.target;
            document.getElementById(target).style.display = 'block';
        });
    });

    function formatCurrency(value) {
        const nums = value.replace(/\D/g, '');
        if (!nums) return '';
        const val = parseInt(nums, 10) / 100;
        return 'R$ ' + val.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }

    function formatCPF(value) {
        const nums = value.replace(/\D/g, '').slice(0, 11);
        return nums.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }

    function formatCEP(value) {
        const nums = value.replace(/\D/g, '').slice(0, 8);
        return nums.replace(/(\d{5})(\d{3})/, '$1-$2');
    }

    function formatDate(value) {
        const nums = value.replace(/\D/g, '').slice(0, 8);
        return nums.replace(/(\d{2})(\d{2})(\d{4})/, '$1/$2/$3');
    }

    document.querySelectorAll('.formatar-moeda').forEach(input => {
        input.addEventListener('blur', (e) => {
            e.target.value = formatCurrency(e.target.value);
        });
    });

    document.querySelectorAll('.formatar-cpf').forEach(input => {
        input.addEventListener('blur', (e) => {
            e.target.value = formatCPF(e.target.value);
        });
    });

    document.querySelectorAll('.formatar-cep').forEach(input => {
        input.addEventListener('blur', (e) => {
            e.target.value = formatCEP(e.target.value);
        });
    });

    document.querySelectorAll('.formatar-data').forEach(input => {
        input.addEventListener('blur', (e) => {
            e.target.value = formatDate(e.target.value);
        });
    });

    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const container = form.closest('.form-container');
            const msgDiv = container.querySelector('.mensagens-erro');
            const aba = form.id === 'alunos-form' ? 'ALUNOS' : 'DOCENTES';

            const formData = new FormData(form);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value;
            });

            if (aba === 'DOCENTES') {
                delete data.nivel;
                delete data.tipo_auxilio;
            }

            if (data.valor && data.valor.startsWith('R$')) {
                data.valor = parseInt(data.valor.replace(/[^\d]/g, ''), 10);
            } else if (data.valor) {
                data.valor = parseInt(data.valor, 10);
            } else {
                data.valor = 0;
            }
            if (isNaN(data.valor)) data.valor = 0;

            try {
                const resp = await fetch('/solicitar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await resp.json();

                if (result.erros && result.erros.length > 0) {
                    msgDiv.style.display = 'block';
                    msgDiv.textContent = result.erros.join('\n');
                } else {
                    msgDiv.style.display = 'none';
                    document.getElementById('tela-formulario').style.display = 'none';
                    document.getElementById('tela-oficio').style.display = 'block';
                    document.getElementById('conteudo-oficio').textContent = result.oficio;
                }
            } catch (err) {
                msgDiv.style.display = 'block';
                msgDiv.textContent = 'Erro ao enviar solicitação.';
            }
        });
    });
});