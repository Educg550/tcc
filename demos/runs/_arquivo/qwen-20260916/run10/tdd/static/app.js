document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('ativa'));
        btn.classList.add('ativa');
        const target = btn.dataset.tab;
        document.querySelectorAll('.tab-content').forEach(c => c.classList.add('oculto'));
        document.getElementById(target).classList.remove('oculto');
    });
});

function formatCpf(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length > 11) value = value.slice(0, 11);
    if (value.length > 9) value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, '$1.$2.$3-$4');
    else if (value.length > 6) value = value.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
    else if (value.length > 3) value = value.replace(/(\d{3})(\d{1,3})/, '$1.$2');
    return value;
}

function formatCep(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length > 8) value = value.slice(0, 8);
    if (value.length > 5) value = value.replace(/(\d{5})(\d{1,3})/, '$1-$2');
    return value;
}

function formatData(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length > 8) value = value.slice(0, 8);
    if (value.length > 4) value = value.replace(/(\d{2})(\d{2})(\d{1,4})/, '$1/$2/$3');
    else if (value.length > 2) value = value.replace(/(\d{2})(\d{1,2})/, '$1/$2');
    return value;
}

function formatValor(input) {
    let value = input.value.replace(/\D/g, '');
    if (!value) return '';
    let number = BigInt(value);
    if (number === 0n) return 'R$ 0,00';
    let formatted = (number / 100n).toLocaleString('pt-BR') + ',' + (number % 100n).toString().padStart(2, '0');
    return 'R$ ' + formatted;
}

function bindFormatter(id, formatter) {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('blur', () => el.value = formatter(el));
}

['al', 'do'].forEach(prefix => {
    bindFormatter(prefix + '_cpf', formatCpf);
    bindFormatter(prefix + '_cep', formatCep);
    bindFormatter(prefix + '_data_nascimento', formatData);
    bindFormatter(prefix + '_valor', formatValor);
});

function collectData(aba) {
    const p = aba === 'ALUNOS' ? 'al_' : 'do_';
    const get = (f) => document.getElementById(p + f).value;
    let valorStr = get('valor').replace(/[^\d]/g, '');
    let valor = parseInt(valorStr || '0');
    
    let data = {
        aba: aba,
        nome: get('nome'),
        nuspp: get('nuspp'),
        programa: get('programa'),
        email: get('email'),
        evento: get('evento'),
        periodo: get('periodo'),
        cidade_evento: get('cidade_evento'),
        estado_evento: get('estado_evento'),
        pais_evento: get('pais_evento'),
        link_evento: get('link_evento'),
        valor: valor,
        detalhamento: get('detalhamento'),
        apresentacao: get('apresentacao'),
        data_nascimento: get('data_nascimento'),
        logradouro: get('logradouro'),
        numero: get('numero'),
        complemento: get('complemento'),
        bairro: get('bairro'),
        cep: get('cep'),
        cidade: get('cidade'),
        estado: get('estado'),
        cpf: get('cpf'),
        rg: get('rg'),
        banco: get('banco'),
        agencia: get('agencia'),
        conta: get('conta')
    };

    if (aba === 'ALUNOS') {
        data.nivel = get('nivel');
        data.tipo_auxilio = get('tipo_auxilio');
    } else {
        data.nivel = "";
        data.tipo_auxilio = "";
    }

    return data;
}

document.querySelectorAll('.btn-enviar').forEach(btn => {
    btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const aba = e.target.closest('.tab-content').id;
        const errosEl = e.target.closest('.tab-content').querySelector('.erros');
        errosEl.innerHTML = '';
        
        const data = collectData(aba);

        try {
            const res = await fetch('/solicitar', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            const json = await res.json();
            
            if (json.erros && json.erros.length > 0) {
                json.erros.forEach(erro => {
                    errosEl.innerHTML += `<div class="erro">${erro}</div>`;
                });
                errosEl.scrollIntoView({behavior: 'smooth', block: 'start'});
            } else if (json.oficio) {
                document.getElementById('form-container').classList.add('oculto');
                document.getElementById('confirmation').classList.remove('oculto');
                document.getElementById('oficio').textContent = json.oficio;
                window.scrollTo(0,0);
            }
        } catch (err) {
            console.error(err);
        }
    });
});