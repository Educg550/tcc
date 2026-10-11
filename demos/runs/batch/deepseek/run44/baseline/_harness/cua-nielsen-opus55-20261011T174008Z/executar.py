import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

ROOT = Path('/home/opuscg550/code/personal/tcc/demos')
sys.path.insert(0, str(ROOT))
os.environ['ANONYMIZED_TELEMETRY'] = 'false'
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')
import httpx
from browser_use import Agent, BrowserSession, ChatOpenRouter, Tools
from harness.models.agentes import load
from harness.models.avaliacao import MAX_PASSOS_CUA, MAX_TOKENS_CUA, OPENROUTER_BASE, SEM_ACOES_CUA, VeredictoCriterio
from harness.models.dominio import Projeto, Requisito

MODEL = 'anthropic/claude-opus-5.5'
REQUISITO = Requisito(ROOT / 'requisitos/01-formulario-docentes-deepseek')
CRITERIO, = REQUISITO.subjetivos
VIEWPORT = {'width': 1366, 'height': 768}


def contabilizar(chamadas):
    usos = [c['usage'] for c in chamadas if c.get('usage')]
    completo = bool(chamadas) and all((c.get('usage') or {}).get('cost') is not None for c in chamadas)
    return {
        'api_calls': len(chamadas),
        'input_tokens': sum(u.get('prompt_tokens', 0) for u in usos),
        'output_tokens': sum(u.get('completion_tokens', 0) for u in usos),
        'total_tokens': sum(u.get('total_tokens', 0) for u in usos),
        'cost_usd': round(sum(u['cost'] for u in usos), 9) if completo else None,
        'confirmed_cost_usd': round(sum(u.get('cost') or 0 for u in usos), 9),
        'cost_complete': completo,
        'cost_source': 'OpenRouter response usage.cost, including judge',
    }


async def executar(run):
    projeto = Projeto(ROOT / f'runs/batch/deepseek/run{run}/baseline', REQUISITO.alvo)
    started = datetime.now(timezone.utc)
    destino = projeto.saida / ('cua-nielsen-opus55-' + started.strftime('%Y%m%dT%H%M%SZ'))
    destino.mkdir(parents=True)
    (destino / 'executar.py').write_text(Path(__file__).read_text(), encoding='utf-8')
    chamadas, erros = [], []
    agente = None
    inicio_cua = None
    duracao_cua = None

    def salvar(nome, dados):
        (destino / nome).write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding='utf-8')

    async def capturar(response):
        if '/chat/completions' not in str(response.url):
            return
        await response.aread()
        dados = response.json()
        registro = {k: dados.get(k) for k in ('id', 'model', 'provider', 'usage', 'error', 'choices')}
        registro['http_status'] = response.status_code
        chamadas.append(registro)
        with (destino / 'api-usage.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(registro, ensure_ascii=False) + '\n')
        if response.is_error or dados.get('error'):
            erros.append(f"API HTTP {response.status_code}: {dados.get('error')}")

    async def checkpoint(agent):
        agent.save_history(destino / 'history.json')
        falhas = [e for e in agent.history.errors() if e]
        if falhas:
            erros.extend(e for e in falhas if e not in erros)
            agent.stop()

    inicio = time.perf_counter()
    print(f'INICIO run{run}: {destino}', flush=True)
    try:
        async with httpx.AsyncClient(timeout=120, event_hooks={'response': [capturar]}) as client:
            catalogo = await client.get(OPENROUTER_BASE + '/models')
            catalogo.raise_for_status()
            modelo = next((m for m in catalogo.json()['data'] if m['id'] == MODEL), None)
            if modelo is None:
                raise RuntimeError(f'Modelo solicitado indisponível no catálogo: {MODEL}')
            salvar('model.json', modelo)
            with projeto.rodando('-nielsen-opus55-' + started.strftime('%Y%m%dT%H%M%SZ')) as url:
                prompt = load('cua_task').format(base_url=url, acao=CRITERIO.acao, resultado_esperado=CRITERIO.resultado_esperado)
                (destino / 'prompt.md').write_text(prompt, encoding='utf-8')
                agente = Agent(
                    task=prompt,
                    llm=ChatOpenRouter(model=MODEL, api_key=os.environ['OPENROUTER_API_KEY'],
                        base_url=OPENROUTER_BASE, http_client=client, max_retries=0,
                        extra_body={'max_tokens': MAX_TOKENS_CUA, 'usage': {'include': True}}),
                    tools=Tools(exclude_actions=SEM_ACOES_CUA),
                    use_thinking=False, max_failures=1, final_response_after_failure=False,
                    browser_session=BrowserSession(headless=True, viewport=VIEWPORT, device_scale_factor=1),
                    output_model_schema=VeredictoCriterio, generate_gif=False, calculate_cost=True,
                    file_system_path=str(destino / 'agent-files'),
                )
                inicio_cua = time.perf_counter()
                await agente.run(max_steps=MAX_PASSOS_CUA, on_step_end=checkpoint)
                duracao_cua = time.perf_counter() - inicio_cua
    except (Exception, KeyboardInterrupt) as erro:
        erros.append(f'{type(erro).__name__}: {erro}')
    finally:
        if inicio_cua is not None and duracao_cua is None:
            duracao_cua = time.perf_counter() - inicio_cua
        history = agente.history if agente else None
        v = history.structured_output if history else None
        if agente:
            agente.save_history(destino / 'history.json')
        resultado = {
            'configured_model': MODEL, 'project': str(projeto.raiz),
            'criterion': CRITERIO.identificador, 'browser_use_version': version('browser-use'),
            'viewport': VIEWPORT, 'device_scale_factor': 1,
            'started_at': started.isoformat(), 'ended_at': datetime.now(timezone.utc).isoformat(),
            'duration_s': round(time.perf_counter() - inicio, 2),
            'cua_duration_s': round(duracao_cua, 2) if duracao_cua is not None else None,
            'num_steps': history.number_of_steps() if history else 0,
            **contabilizar(chamadas),
            'errors': erros, 'completed': bool(v and v.passou and not erros),
            'veredicto': v.model_dump() if v else None,
            'browser_use_usage': history.usage.model_dump() if history and history.usage else None,
        }
        salvar('resultado.json', resultado)
        if v:
            (destino / 'relatorio.md').write_text(v.evidencia, encoding='utf-8')
        print('RESULTADO: ' + json.dumps(resultado, ensure_ascii=False), flush=True)
    return resultado['completed']


async def main():
    for run in (44, 35):
        if not await executar(run):
            raise SystemExit('Cua interrompido; nenhuma nova tentativa ou outra run será iniciada.')


if __name__ == '__main__':
    if '--check' in sys.argv:
        exemplo = {'usage': {'prompt_tokens': 2, 'completion_tokens': 3, 'total_tokens': 5, 'cost': 0.1}}
        assert contabilizar([exemplo, exemplo])['cost_usd'] == 0.2
        assert contabilizar([exemplo, {'usage': {}}])['cost_usd'] is None
        assert contabilizar([exemplo, {'usage': None}])['confirmed_cost_usd'] == 0.1
        assert CRITERIO.identificador == 'C1'
        assert all((ROOT / f'runs/batch/deepseek/run{n}/baseline/app.py').is_file() for n in (44, 35))
        assert os.environ.get('OPENROUTER_API_KEY'), 'OPENROUTER_API_KEY ausente'
        print('Checks locais OK; nenhuma chamada ao modelo.')
    else:
        asyncio.run(main())
