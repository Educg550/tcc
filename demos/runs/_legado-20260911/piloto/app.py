from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse

app = FastAPI()

def format_currency(centavos: int) -> str:
    reais = centavos // 100
    centavos_rest = centavos % 100
    # Formata com separador de milhar e dois dígitos decimais
    return f"R$ {reais:,}.{centavos_rest:02d}".replace(",", ".").replace(".", ",", 1) if reais >= 1000 else f"R$ {reais},{centavos_rest:02d}"

def format_currency_br(value: int) -> str:
    if value < 0:
        raise ValueError
    s = f"{value:0{3}d}"
    reais = s[:-2]
    centavos = s[-2:]
    # separador de milhar
    partes = []
    while len(reais) > 3:
        partes.insert(0, reais[-3:])
        reais = reais[:-3]
    partes.insert(0, reais)
    reais_str = ".".join(partes)
    return f"R$ {reais_str},{centavos}"

HTML_FORM = '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body>
  {error}
  <form method="post">
    <label>NOME COMPLETO - SEM ABREVIAR</label><br>
    <input type="text" name="NOME COMPLETO - SEM ABREVIAR" placeholder="NOME COMPLETO - SEM ABREVIAR" value="{v1}"><br>
    <label>N. USP</label><br>
    <input type="text" name="N. USP" placeholder="N. USP" value="{v2}"><br>
    <label>PROGRAMA</label><br>
    <input type="text" name="PROGRAMA" placeholder="PROGRAMA" value="{v3}"><br>
    <label>NOME DO EVENTO</label><br>
    <input type="text" name="NOME DO EVENTO" placeholder="NOME DO EVENTO" value="{v4}"><br>
    <label>PERÍODO DO EVENTO</label><br>
    <input type="text" name="PERÍODO DO EVENTO" placeholder="PERÍODO DO EVENTO" value="{v5}"><br>
    <label>CIDADE DO EVENTO</label><br>
    <input type="text" name="CIDADE DO EVENTO" placeholder="CIDADE DO EVENTO" value="{v6}"><br>
    <label>VALOR SOLICITADO</label><br>
    <input type="text" name="VALOR SOLICITADO" placeholder="VALOR SOLICITADO" value="{v7}"><br>
    <button type="submit">Enviar solicitação</button>
  </form>
</body>
</html>'''

HTML_SUCCESS = '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body>
  <h1>Solicitação registrada</h1>
  <pre>
Interessada(o): {nome} - {nusp}
Assunto: Solicitação de Auxílio Financeiro
Programa: {programa}
Evento: {evento}
Período: {periodo}
Local: {cidade}
Valor solicitado: {valor}
  </pre>
</body>
</html>'''

@app.get("/", response_class=HTMLResponse)
async def form_get():
    return HTML_FORM.format(error="", v1="", v2="", v3="", v4="", v5="", v6="", v7="")

@app.post("/", response_class=HTMLResponse)
async def form_post(
    request: Request,
    nome: str = Form("", alias="NOME COMPLETO - SEM ABREVIAR"),
    nusp: str = Form("", alias="N. USP"),
    programa: str = Form("", alias="PROGRAMA"),
    evento: str = Form("", alias="NOME DO EVENTO"),
    periodo: str = Form("", alias="PERÍODO DO EVENTO"),
    cidade: str = Form("", alias="CIDADE DO EVENTO"),
    valor: str = Form("", alias="VALOR SOLICITADO"),
):
    if not nome or not nusp or not programa or not evento or not periodo or not cidade or not valor:
        return HTML_FORM.format(error="<p>Preencha todos os campos</p>", v1=nome, v2=nusp, v3=programa, v4=evento, v5=periodo, v6=cidade, v7=valor)
    if not nusp.isdigit():
        return HTML_FORM.format(error="<p>N. USP deve conter apenas n\u00fameros</p>", v1=nome, v2=nusp, v3=programa, v4=evento, v5=periodo, v6=cidade, v7=valor)
    try:
        valor_int = int(valor)
        if valor_int <= 0:
            raise ValueError
    except ValueError:
        return HTML_FORM.format(error="<p>Valor solicitado deve ser maior que 0</p>", v1=nome, v2=nusp, v3=programa, v4=evento, v5=periodo, v6=cidade, v7=valor)
    valor_formatado = format_currency_br(valor_int)
    return HTML_SUCCESS.format(nome=nome, nusp=nusp, programa=programa, evento=evento, periodo=periodo, cidade=cidade, valor=valor_formatado)
