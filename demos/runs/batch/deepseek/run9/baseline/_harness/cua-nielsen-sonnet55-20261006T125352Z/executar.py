import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/opuscg550/code/personal/tcc/demos')
sys.path.insert(0, str(ROOT))
os.environ['ANONYMIZED_TELEMETRY'] = 'false'
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')
import httpx
from browser_use import Agent, BrowserSession, ChatOpenAI, Tools
from harness.models.agentes import load
from harness.models.avaliacao import MAX_PASSOS_CUA, MAX_TOKENS_CUA, OPENROUTER_BASE, VeredictoCriterio
from harness.models.dominio import Projeto, Requisito

MODEL = 'anthropic/claude-sonnet-5.5'
requisito = Requisito(ROOT / 'requisitos/01-formulario-docentes-deepseek')
projeto = Projeto(ROOT / 'runs/batch/deepseek/run9/baseline', requisito.alvo)
criterio, = requisito.subjetivos
started = datetime.now(timezone.utc)
destino = projeto.saida / ('cua-nielsen-sonnet55-' + started.strftime('%Y%m%dT%H%M%SZ'))
destino.mkdir(parents=True)
print(f'ARTEFATOS: {destino}', flush=True)
chamadas = []

def salvar(nome, dados):
    (destino / nome).write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding='utf-8')

async def capturar(response):
    if '/chat/completions' not in str(response.url):
        return
    await response.aread()
    dados = response.json()
    registro = {k: dados.get(k) for k in ('id', 'model', 'provider', 'usage', 'error')}
    registro['http_status'] = response.status_code
    registro['choices'] = dados.get('choices')
    chamadas.append(registro)
    with (destino / 'api-usage.jsonl').open('a') as f:
        f.write(json.dumps(registro, ensure_ascii=False) + '\n')

async def main():
    async with httpx.AsyncClient(timeout=120, event_hooks={'response': [capturar]}) as client:
        catalogo = await client.get(OPENROUTER_BASE + '/models')
        catalogo.raise_for_status()
        modelo = next((m for m in catalogo.json()['data'] if m['id'] == MODEL), None)
        if modelo is None:
            raise RuntimeError(f'Modelo solicitado indisponível no catálogo: {MODEL}')
        salvar('model.json', modelo)
        inicio = time.perf_counter()
        with projeto.rodando('-nielsen-' + started.strftime('%Y%m%dT%H%M%SZ')) as url:
            prompt = load('cua_task').format(base_url=url, acao=criterio.acao, resultado_esperado=criterio.resultado_esperado)
            (destino / 'prompt.md').write_text(prompt, encoding='utf-8')
            llm = ChatOpenAI(model=MODEL, base_url=OPENROUTER_BASE, api_key=os.environ['OPENROUTER_API_KEY'], max_completion_tokens=MAX_TOKENS_CUA, http_client=client)
            tools = Tools(exclude_actions=['search', 'upload_file', 'switch', 'close', 'extract', 'search_page', 'find_elements', 'save_as_pdf', 'write_file', 'replace_file', 'read_file', 'evaluate'])
            agente = Agent(task=prompt, llm=llm, tools=tools, max_failures=1, browser_session=BrowserSession(headless=True, viewport={'width': 1366, 'height': 768}), output_model_schema=VeredictoCriterio, generate_gif=False, calculate_cost=True, file_system_path=str(destino / 'agent-files'))
            async def checkpoint(agent):
                agent.save_history(destino / 'history.json')
            inicio_cua = time.perf_counter()
            try:
                history = await agente.run(max_steps=MAX_PASSOS_CUA, on_step_end=checkpoint)
            finally:
                agente.save_history(destino / 'history.json')
            duracao_cua = time.perf_counter() - inicio_cua
        duration = time.perf_counter() - inicio
        usos = [c['usage'] for c in chamadas if c.get('usage')]
        custos = [u.get('cost') for u in usos]
        resultado = {
            'configured_model': MODEL, 'project': str(projeto.raiz), 'structured_output_mode': 'strict_schema_navigation_tools_only',
            'started_at': started.isoformat(), 'ended_at': datetime.now(timezone.utc).isoformat(),
            'duration_s': round(duration, 2), 'cua_duration_s': round(duracao_cua, 2),
            'num_steps': history.number_of_steps(), 'api_calls': len(chamadas),
            'input_tokens': sum(u.get('prompt_tokens', 0) for u in usos),
            'output_tokens': sum(u.get('completion_tokens', 0) for u in usos),
            'total_tokens': sum(u.get('total_tokens', 0) for u in usos),
            'cost_usd': sum(custos) if custos and all(c is not None for c in custos) else None,
            'cost_source': 'OpenRouter response usage.cost',
            'browser_use_usage': history.usage.model_dump() if history.usage else None,
            'veredicto': history.structured_output.model_dump() if history.structured_output else None,
        }
        salvar('resultado.json', resultado)
        if history.structured_output:
            (destino / 'relatorio.md').write_text(history.structured_output.evidencia, encoding='utf-8')
        print('RESULTADO: ' + json.dumps(resultado, ensure_ascii=False), flush=True)

asyncio.run(main())
