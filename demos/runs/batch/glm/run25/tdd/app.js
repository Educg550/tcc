document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    var CAMPOS_OPCIONAIS = ['link_evento', 'complemento'];

    function formatarCPF(valor) {
        var d = valor.replace(/\D/g, '').slice(0, 11);
        if (d.length > 9) {
            return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
        }
        if (d.length > 6) {
            return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
        }
        if (d.length > 3) {
            return d.slice(0, 3) + '.' + d.slice(3);
        }
        return d;
    }

    function formatarCEP(valor) {
        var d = valor.replace(/\D/g, '').slice(0, 8);
        if (d.length > 5) {
            return d.slice(0, 5) + '-' + d.slice(5);
        }
        return d;
    }

    function formatarData(valor) {
        var d = valor.replace(/\D/g, '').slice(0, 8);
        if (d.length > 4) {
            return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
        }
        if (d.length > 2) {
            return d.slice(0, 2) + '/' + d.slice(2);
        }
        return d;
    }

    function formatarValor(valor) {
        var d = valor.replace(/\D/g, '');
        if (!d) {
            return '';
        }
        var centavos = parseInt(d, 10);
        var reais = Math.floor(centavos / 100);
        var resto = centavos % 100;
        var reaisStr = reais.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        return 'R$ ' + reaisStr + ',' + ('0' + resto).slice(-2);
    }

    function mostrarErros(aba, erros) {
        var area = document.getElementById('erros-' + aba);
        area.innerHTML = '';
        erros.forEach(function (msg) {
            var p = document.createElement('p');
            p.textContent = msg;
            area.appendChild(p);
        });
    }

    function trocarAba(nome) {
        var botoes = document.querySelectorAll('.tab-button');
        botoes.forEach(function (btn) {
            btn.classList.toggle('active', btn.dataset.tab === nome);
        });
        var conteudos = document.querySelectorAll('.tab-content');
        conteudos.forEach(function (c) {
            c.classList.toggle('active', c.id === 'tab-' + nome);
        });
    }

    document.querySelectorAll('.tab-button').forEach(function (btn) {
        btn.addEventListener('click', function () {
            trocarAba(btn.dataset.tab);
        });
    });

    function montarFormularios() {
        var configs = {
            alunos: [
                ['nome_completo', 'NOME COMPLETO - SEM ABREVIAR', 'text', 'Maria da Silva'],
                ['n_usp', 'N. USP', 'text', '12345678'],
                ['programa', 'PROGRAMA', 'text', 'Matemática Aplicada'],
                ['nivel', 'NÍVEL', 'select', ['Mestrado', 'Doutorado']],
                ['tipo_auxilio', 'TIPO DE AUXÍLIO', 'select', ['Participação em evento', 'Banca de exame ou defesa', 'Outro']],
                ['email', 'E-MAIL', 'email', 'maria@ime.usp.br'],
                ['nome_evento', 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', 'text', 'Congresso Nacional'],
                ['periodo', 'PERÍODO DO EVENTO, EXAME OU DEFESA', 'text', '10 a 12 de julho de 2025'],
                ['cidade_evento', 'CIDADE DO EVENTO, EXAME OU DEFESA', 'text', 'São Paulo'],
                ['estado_evento', 'ESTADO DO EVENTO, EXAME OU DEFESA', 'text', 'SP'],
                ['pais_evento', 'PAÍS DO EVENTO, EXAME OU DEFESA', 'text', 'Brasil'],
                ['link_evento', 'LINK DO EVENTO, EXAME OU DEFESA', 'text', 'congreso.br'],
                ['valor_solicitado', 'VALOR SOLICITADO (R$)', 'text', '1500'],
                ['detalhamento', 'DETALHAMENTO DO PEDIDO', 'textarea', 'Inscrição e hospedagem'],
                ['apresentacao', 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', 'select', ['Pôster', 'Apresentação oral', 'Outra', 'Não irá apresentar trabalho']]
            ],
            docentes: [
                ['nome_completo', 'NOME COMPLETO - SEM ABREVIAR', 'text', 'João da Silva'],
                ['n_usp', 'N. USP', 'text', '87654321'],
                ['programa', 'PROGRAMA', 'text', 'Matemática'],
                ['email', 'E-MAIL', 'email', 'joao@ime.usp.br'],
                ['nome_evento', 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', 'text', 'Seminário'],
                ['periodo', 'PERÍODO DO EVENTO, EXAME OU DEFESA', 'text', '5 de outubro'],
                ['cidade_evento', 'CIDADE DO EVENTO, EXAME OU DEFESA', 'text', 'Campinas'],
                ['estado_evento', 'ESTADO DO EVENTO, EXAME OU DEFESA', 'text', 'SP'],
                ['pais_evento', 'PAÍS DO EVENTO, EXAME OU DEFESA', 'text', 'Brasil'],
                ['link_evento', 'LINK DO EVENTO, EXAME OU DEFESA', 'text', 'sem site'],
                ['valor_solicitado', 'VALOR SOLICITADO (R$)', 'text', '2500'],
                ['detalhamento', 'DETALHAMENTO DO PEDIDO', 'textarea', 'Passagem'],
                ['apresentacao', 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', 'select', ['Pôster', 'Apresentação oral', 'Outra', 'Não irá apresentar trabalho']]
            ]
        };

        Object.keys(configs).forEach(function (aba) {
            var form = document.getElementById('form-' + aba);
            var html = '';
            configs[aba].forEach(function (c) {
                html += '<div class="form-group"><label>' + c[1] + '</label>';
                if (c[2] === 'select') {
                    html += '<select name="' + c[0] + '">';
                    c[3].forEach(function (op) {
                        html += '<option value="' + op + '">' + op + '</option>';
                    });
                    html += '</select></div>';
                } else if (c[2] === 'textarea') {
                    html += '<textarea name="' + c[0] + '" rows="2">' + c[3] + '</textarea></div>';
                } else {
                    html += '<input type="' + c[2] + '" name="' + c[0] + '" placeholder="' + c[3] + '"></div>';
                }
            });
            form.insertBefore(htmlToFragment(html), form.firstChild.nextSibling);
        });
    }

    function htmlToFragment(html) {
        var t = document.createElement('template');
        t.innerHTML = html;
        return t.content;
    }

    montarFormularios();

    document.querySelectorAll('input[name=valor_solicitado]').forEach(function (inp) {
        inp.addEventListener('blur', function () {
            inp.value = formatarValor(inp.value);
        });
    });

    document.querySelectorAll('input[name=cpf]').forEach(function (inp) {
        inp.addEventListener('blur', function () {
            inp.value = formatarCPF(inp.value);
        });
    });

    document.querySelectorAll('input[name=cep]').forEach(function (inp) {
        inp.addEventListener('blur', function () {
            inp.value = formatarCEP(inp.value);
        });
    });

    document.querySelectorAll('input[name=data_nascimento]').forEach(function (inp) {
        inp.addEventListener('blur', function () {
            inp.value = formatarData(inp.value);
        });
    });

    ['alunos', 'docentes'].forEach(function (aba) {
        document.getElementById('form-' + aba).addEventListener('submit', function (e) {
            e.preventDefault();
            var dados = { aba: aba };
            new FormData(e.target).forEach(function (v, k) {
                dados[k] = v;
            });
            fetch('/api/solicitacao', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dados)
            }).then(function (r) { return r.json(); }).then(function (corpo) {
                if (corpo.valido) {
                    document.getElementById('oficio').textContent = corpo.oficio;
                    document.querySelectorAll('.tab-content').forEach(function (c) { c.classList.add('hidden'); });
                    document.querySelector('.tabs').classList.add('hidden');
                    document.getElementById('resultado').classList.remove('hidden');
                } else {
                    mostrarErros(aba, corpo.erros);
                }
            });
        });
    });
});
