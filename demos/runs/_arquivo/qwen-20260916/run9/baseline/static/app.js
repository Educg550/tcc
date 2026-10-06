function formatCpf(input) {
    let v = input.value.replace(/\D/g, '');
    v = v.substring(0, 11);
    v = v.replace(/(\d{3})(\d)/, '$1.$2');
    v = v.replace(/(\d{3})(\d)/, '$1.$2');
    v = v.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    input.value = v;
}

function formatCep(input) {
    let v = input.value.replace(/\D/g, '');
    v = v.substring(0, 8);
    v = v.replace(/(\d{5})(\d{1,3})/, '$1-$2');
    input.value = v;
}

function formatDate(input) {
    let v = input.value.replace(/\D/g, '');
    v = v.substring(0, 8);
    v = v.replace(/(\d{2})(\d)/, '$1/$2');
    v = v.replace(/(\d{2})(\d{2})(\d)/, '$1/$2/$3');
    input.value = v;
}

function formatMoney(input) {
    let v = input.value.replace(/\D/g, '');
    if (!v) {
        input.value = '';
        return;
    }
    let num = parseInt(v, 10);
    let integerPart = Math.floor(num / 100);
    let cents = num % 100;
    let intStr = integerPart.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    input.value = `R$ ${intStr},${cents.toString().padStart(2, '0')}`;
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.cpf-input').forEach(el => el.addEventListener('blur', e => formatCpf(e.target)));
    document.querySelectorAll('.cep-input').forEach(el => el.addEventListener('blur', e => formatCep(e.target)));
    document.querySelectorAll('.date-input').forEach(el => el.addEventListener('blur', e => formatDate(e.target)));
    document.querySelectorAll('input[name="valor_solicitado"]').forEach(el => el.addEventListener('blur', e => formatMoney(e.target)));

    let activeTab = 'alunos';

    function switchTab(tab) {
        activeTab = tab;
        document.getElementById('tab-alunos').classList.toggle('active', tab === 'alunos');
        document.getElementById('tab-docentes').classList.toggle('active', tab === 'docentes');
        document.getElementById('form-alunos').style.display = tab === 'alunos' ? 'flex' : 'none';
        document.getElementById('form-docentes').style.display = tab === 'docentes' ? 'flex' : 'none';
        document.getElementById('errors-box').innerHTML = '';
    }

    document.getElementById('tab-alunos').addEventListener('click', () => switchTab('alunos'));
    document.getElementById('tab-docentes').addEventListener('click', () => switchTab('docentes'));

    document.getElementById('form-alunos').addEventListener('submit', e => handleFormSubmit(e, 'alunos'));
    document.getElementById('form-docentes').addEventListener('submit', e => handleFormSubmit(e, 'docentes'));

    async function handleFormSubmit(e, tab) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        data.aba = tab;

        try {
            const res = await fetch('/api/solicitar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const json = await res.json();

            if (json.success) {
                document.getElementById('app-container').style.display = 'none';
                document.getElementById('success-container').style.display = 'flex';
                document.getElementById('oficio-content').textContent = json.oficio;
            } else {
                document.getElementById('errors-box').innerHTML = json.errors.join('\n');
            }
        } catch (err) {
            console.error(err);
        }
    }
});
