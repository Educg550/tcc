const campos = [
  {id:'nomeCompleto', rotulo:'NOME COMPLETO - SEM ABREVIAR', tipo:'text', ph:'Maria da Silva Santos', largura:'250px'},
  {id:'numeroUSP', rotulo:'N. USP', tipo:'text', ph:'12345678', largura:'100px'},
  {id:'programa', rotulo:'PROGRAMA', tipo:'text', ph:'Matemática', largura:'150px'},
  {id:'nivel', rotulo:'NÍVEL', tipo:'select', opcoes:['Mestrado','Doutorado'], largura:'110px', alunos:true},
  {id:'tipoAuxilio', rotulo:'TIPO DE AUXÍLIO', tipo:'select', opcoes:['Participação em evento','Banca de exame ou defesa','Outro'], largura:'200px', alunos:true},
  {id:'email', rotulo:'E-MAIL', tipo:'email', ph:'nome@usp.br', largura:'180px'},
  {id:'nomeEvento', rotulo:'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', tipo:'text', ph:'Congresso Brasileiro de Matemática', largura:'250px'},
  {id:'periodo', rotulo:'PERÍODO DO EVENTO, EXAME OU DEFESA', tipo:'text', ph:'10 a 15 de julho de 2024', largura:'180px'},
  {id:'cidadeEvento', rotulo:'CIDADE DO EVENTO, EXAME OU DEFESA', tipo:'text', ph:'São Paulo', largura:'150px'},
  {id:'estadoEvento', rotulo:'ESTADO DO EVENTO, EXAME OU DEFESA', tipo:'text', ph:'SP', largura:'90px'},
  {id:'paisEvento', rotulo:'PAÍS DO EVENTO, EXAME OU DEFESA', tipo:'text', ph:'Brasil', largura:'110px'},
  {id:'linkEvento', rotulo:'LINK DO EVENTO, EXAME OU DEFESA', tipo:'url', ph:'https://evento.com', largura:'180px', opcional:true},
  {id:'valor', rotulo:'VALOR SOLICITADO (R$)', tipo:'text', ph:'R$ 1.500,00', largura:'130px', masc:'moeda'},
  {id:'detalhamento', rotulo:'DETALHAMENTO DO PEDIDO', tipo:'textarea', ph:'Passagem aérea e hospedagem...', largura:'100%'},
  {id:'apresentacao', rotulo:'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', tipo:'select', opcoes:['Pôster','Apresentação oral','Outra','Não irá apresentar trabalho'], largura:'220px'},
  {id:'nascimento', rotulo:'DATA DE NASCIMENTO', tipo:'text', ph:'01/02/1980', largura:'110px', masc:'data'},
  {id:'logradouro', rotulo:'LOGRADOURO', tipo:'text', ph:'Rua do Matão', largura:'200px'},
  {id:'numeroEndereco', rotulo:'NÚMERO', tipo:'text', ph:'1010', largura:'80px'},
  {id:'complemento', rotulo:'COMPLEMENTO', tipo:'text', ph:'Bloco A, sala 12', largura:'140px', opcional:true},
  {id:'bairro', rotulo:'BAIRRO', tipo:'text', ph:'Butantã', largura:'130px'},
  {id:'cep', rotulo:'CEP', tipo:'text', ph:'05508-090', largura:'110px', masc:'cep'},
  {id:'cidadeEndereco', rotulo:'CIDADE', tipo:'text', ph:'São Paulo', largura:'140px'},
  {id:'estadoEndereco', rotulo:'ESTADO', tipo:'text', ph:'SP', largura:'80px'},
  {id:'cpf', rotulo:'CPF (SEPARADOS POR PONTOS E TRAÇO)', tipo:'text', ph:'123.456.789-09', largura:'140px', masc:'cpf'},
  {id:'rg', rotulo:'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', tipo:'text', ph:'12.345.678-9', largura:'170px'},
  {id:'banco', rotulo:'NOME DO BANCO', tipo:'text', ph:'Banco do Brasil', largura:'160px'},
  {id:'agencia', rotulo:'NÚMERO DA AGÊNCIA', tipo:'text', ph:'1234', largura:'130px'},
  {id:'conta', rotulo:'NÚMERO DA CONTA', tipo:'text', ph:'12345-6', largura:'130px'}
];

const blocos = [
  {titulo:'SOLICITANTE E EVENTO', ids:['nomeCompleto','numeroUSP','programa','nivel','tipoAuxilio','email','nomeEvento','periodo','cidadeEvento','estadoEvento','paisEvento','linkEvento','valor','detalhamento','apresentacao']},
  {titulo:'ENDEREÇO DO SOLICITANTE', ids:['nascimento','logradouro','numeroEndereco','complemento','bairro','cep','cidadeEndereco','estadoEndereco']},
  {titulo:'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO', ids:['cpf','rg','banco','agencia','conta']}
];

function campoHTML(c, aba) {
  let inp;
  const id = aba + '-' + c.id;
  if (c.tipo === 'select') {
    inp = `<select id="${id}">` + c.opcoes.map(o=>`<option>${o}</option>`).join('') + '</select>';
  } else if (c.tipo === 'textarea') {
    inp = `<textarea id="${id}" placeholder="${c.ph}"></textarea>`;
  } else {
    inp = `<input type="${c.tipo}" id="${id}" placeholder="${c.ph}">`;
  }
  const opc = c.opcional ? ' <small>(opcional)</small>' : '';
  const est = c.largura === '100%' ? 'width:100%' : `width:${c.largura}`;
  return `<div class="campo" style="${est}"><label for="${id}">${c.rotulo}${opc}</label>${inp}</div>`;
}

function formHTML(aba) {
  let h = `<div id="erros-${aba}" class="erros"></div>`;
  for (const b of blocos) {
    let cs = b.ids.map(i=>campos.find(c=>c.id===i));
    if (aba === 'DOCENTES') cs = cs.filter(c=>!c.alunos);
    let linhas = [];
    if (aba === 'ALUNOS') {
      linhas = [['nomeCompleto','numeroUSP','programa','nivel','tipoAuxilio'],
                ['email','nomeEvento','periodo'],
                ['cidadeEvento','estadoEvento','paisEvento','linkEvento','valor'],
                ['detalhamento'],['apresentacao']];
    } else {
      linhas = [['nomeCompleto','numeroUSP','programa'],
                ['email','nomeEvento','periodo'],
                ['cidadeEvento','estadoEvento','paisEvento','linkEvento','valor'],
                ['detalhamento'],['apresentacao']];
    }
    if (b.titulo !== 'SOLICITANTE E EVENTO') {
      linhas = [b.ids.slice()];
    }
    h += `<section class="bloco"><h2>${b.titulo}</h2>`;
    for (const l of linhas) {
      h += '<div class="linha">';
      for (const id of l) {
        const c = campos.find(c=>c.id===id);
        h += campoHTML(c, aba);
      }
      h += '</div>';
    }
    h += '</section>';
  }
  h += `<button id="botao-${aba}" class="botao" onclick="enviar('${aba}')">Enviar solicitação</button>`;
  return h;
}

function render() {
  const m = document.getElementById('conteudo');
  m.innerHTML = '<div id="abas" class="abas">' +
    '<div class="aba ativa" id="aba-ALUNOS" onclick="mudar('ALUNOS')">ALUNOS</div>' +
    '<div class="aba" id="aba-DOCENTES" onclick="mudar('DOCENTES')">DOCENTES</div></div>' +
    `<div id="form-ALUNOS" class="formulario">${formHTML('ALUNOS')}</div>` +
    `<div id="form-DOCENTES" class="formulario oculto">${formHTML('DOCENTES')}</div>`;
  document.getElementById('valor-ALUNOS').addEventListener('blur', ()=>formatarMoeda('valor-ALUNOS'));
  document.getElementById('valor-DOCENTES').addEventListener('blur', ()=>formatarMoeda('valor-DOCENTES'));
  document.getElementById('cpf-ALUNOS').addEventListener('blur', ()=>formatarCPF('cpf-ALUNOS'));
  document.getElementById('cpf-DOCENTES').addEventListener('blur', ()=>formatarCPF('cpf-DOCENTES'));
  document.getElementById('cep-ALUNOS').addEventListener('blur', ()=>formatarCEP('cep-ALUNOS'));
  document.getElementById('cep-DOCENTES').addEventListener('blur', ()=>formatarCEP('cep-DOCENTES'));
  document.getElementById('nascimento-ALUNOS').addEventListener('blur', ()=>formatarData('nascimento-ALUNOS'));
  document.getElementById('nascimento-DOCENTES').addEventListener('blur', ()=>formatarData('nascimento-DOCENTES'));
}

function mudar(aba) {
  document.getElementById('aba-ALUNOS').classList.toggle('ativa', aba==='ALUNOS');
  document.getElementById('aba-DOCENTES').classList.toggle('ativa', aba==='DOCENTES');
  document.getElementById('form-ALUNOS').classList.toggle('oculto', aba!=='ALUNOS');
  document.getElementById('form-DOCENTES').classList.toggle('oculto', aba!=='DOCENTES');
}

function formatarMoeda(id) {
  const el = document.getElementById(id);
  const d = el.value.replace(/\D/g,'');
  if (!d) { el.value=''; return; }
  let n = parseInt(d,10)/100;
  el.value = 'R$ ' + n.toFixed(2).replace('.',',').replace(/\B(?=(\d{3})+(?!\d))/g,'.');
}

function formatarCPF(id) {
  const el = document.getElementById(id);
  const d = el.value.replace(/\D/g,'').slice(0,11);
  el.value = d.replace(/(\d{3})(\d)/,'$1.$2').replace(/(\d{3})\.(\d{3})(\d)/,'$1.$2.$3').replace(/\.\d{3}(\d{2})$/,'-$1');
}

function formatarCEP(id) {
  const el = document.getElementById(id);
  const d = el.value.replace(/\D/g,'').slice(0,8);
  el.value = d.length>5 ? d.slice(0,5)+'-'+d.slice(5) : d;
}

function formatarData(id) {
  const el = document.getElementById(id);
  const d = el.value.replace(/\D/g,'').slice(0,8);
  if (d.length===8) el.value = d.slice(0,2)+'/'+d.slice(2,4)+'/'+d.slice(4);
  else el.value = d;
}

async function enviar(aba) {
  const dados = {aba};
  for (const c of campos) {
    if (aba==='DOCENTES' && c.alunos) continue;
    const el = document.getElementById(aba+'-'+c.id);
    dados[c.id] = el ? el.value : '';
  }
  const r = await fetch('/api/solicitar', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(dados)});
  const resp = await r.json();
  const er = document.getElementById('erros-'+aba);
  if (!resp.ok) {
    er.innerHTML = resp.erros.map(e=>`<p>${e}</p>`).join('');
    return;
  }
  const m = document.getElementById('conteudo');
  m.innerHTML = `<div id="abas" class="abas"></div><h2 class="titulo">Solicitação registrada</h2><pre class="oficio">${resp.oficio}</pre>`;
}

render();
