document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        document.querySelectorAll('form').forEach(f => f.classList.remove('active'));
        document.getElementById('form-' + tab.dataset.tipo).classList.add('active');
    });
});

function formatarCampo(e) {
    let v = e.target.value.replace(/\D/g, '');
    if (!v) { e.target.value = ''; return; }
    switch(e.target.name) {
        case 'valor_solicitado':
            e.target.value = 'R$ ' + (parseInt(v) / 100).toLocaleString('pt-BR', {minimumFractionDigits: 2});
            break;
        case 'cpf':
            e.target.value = v.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
            break;
        case 'cep':
            e.target.value = v.length > 5 ? v.slice(0,5) + '-' + v.slice(5) : v;
            break;
        case 'data_nascimento':
            let d = v.slice(0,2), m = v.slice(2,4), a = v.slice(4,8);
            e.target.value = d + (m ? '/' + m : '') + (a ? '/' + a : '');
            break;
    }
}

document.addEventListener('blur', e => {
    if (['valor_solicitado','cpf','cep','data_nascimento'].includes(e.target.name)) formatarCampo(e);
}, true);

async function enviarForm(form) {
    const dados = Object.fromEntries(new FormData(form));
    if (dados.valor_solicitado) {
        const limpo = dados.valor_solicitado.replace(/\D/g, '');
        dados.valor_solicitado = limpo ? parseInt(limpo) / 100 : 0;
    }
    const res = await fetch('/api/solicitacao', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(dados)
    });
    const data = await res.json();
    if (res.ok) {
        document.getElementById('resultado').innerText = 'Solicitação registrada\n\n' + data.oficio;
        document.getElementById('resultado').style.display = 'block';
        form.style.display = 'none';
        document.querySelector('.tabs').style.display = 'none';
    } else {
        const divErros = form.querySelector('.erros');
        divErros.innerHTML = data.erros.map(e => `<div>${e}</div>`).join('');
    }
}

document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', e => {
        e.preventDefault();
        enviarForm(form);
    });
});
