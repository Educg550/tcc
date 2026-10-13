import asyncio
import json
import os
import sys
import shutil
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
import browser_use.agent.service as agent_service
from browser_use.agent.judge import construct_judge_messages
from harness.models.agentes import load
from harness.models.avaliacao import MAX_PASSOS_CUA, MAX_TOKENS_CUA, OPENROUTER_BASE, SEM_ACOES_CUA, VeredictoCriterio
from harness.models.dominio import Projeto, Requisito

MODEL = 'anthropic/claude-opus-5.5'
REQUISITO = Requisito(ROOT / 'requisitos/01-formulario-docentes-deepseek')
CRITERIO, = REQUISITO.subjetivos
VIEWPORT = {'width': 1366, 'height': 768}
PARAMETROS_LLM = {'max_tokens': MAX_TOKENS_CUA, 'extra_body': {'usage': {'include': True}}}


# O judge padrão só recebe as dez últimas capturas, omitindo o percurso ALUNOS.
def judge_completo(**kwargs):
    kwargs['max_images'] = len(kwargs['screenshot_paths'])
    return construct_judge_messages(**kwargs)


agent_service.construct_judge_messages = judge_completo


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
    projeto = Projeto(ROOT / f'runs/batch/{run}', REQUISITO.alvo)
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
    print(f'INICIO {run}: {destino}', flush=True)
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
                        extra_body=PARAMETROS_LLM),
                    tools=Tools(exclude_actions=SEM_ACOES_CUA),
                    use_thinking=False, max_failures=1, final_response_after_failure=False,
                    browser_session=BrowserSession(headless=True, viewport=VIEWPORT, device_scale_factor=1, allowed_domains=['localhost']),
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
            'judge_capture_policy': 'all', 'judge': history.judgement() if history else None,
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
        if history:
            capturas = []
            for i, step in enumerate(history.history, 1):
                origem = step.state.screenshot_path
                if origem:
                    foto = destino / 'screenshots' / f'step_{i}.png'
                    foto.parent.mkdir(exist_ok=True)
                    shutil.copyfile(origem, foto)
                    capturas.append({'step': i, 'original_path': origem, 'saved_path': str(foto.relative_to(destino))})
            salvar('capturas.json', capturas)
            salvar('judge.json', history.judgement())
            resultado['judge_screenshots'] = len(capturas)
        salvar('resultado.json', resultado)
        if v:
            (destino / 'relatorio.md').write_text(v.evidencia, encoding='utf-8')
        print('RESULTADO: ' + json.dumps(resultado, ensure_ascii=False), flush=True)
    return resultado['completed']


async def main():
    for run in ('deepseek/run35/baseline',):
        if not await executar(run):
            raise SystemExit('Cua interrompido; nenhuma nova tentativa ou outra run será iniciada.')


if __name__ == '__main__':
    if '--check' in sys.argv:
        exemplo = {'usage': {'prompt_tokens': 2, 'completion_tokens': 3, 'total_tokens': 5, 'cost': 0.1}}
        assert contabilizar([exemplo, exemplo])['cost_usd'] == 0.2
        assert contabilizar([exemplo, {'usage': {}}])['cost_usd'] is None
        assert contabilizar([exemplo, {'usage': None}])['confirmed_cost_usd'] == 0.1
        assert CRITERIO.identificador == 'C1'
        assert all((ROOT / f'runs/batch/{n}/app.py').is_file() for n in ('deepseek/run35/baseline', 'glm/run19/tdd'))
        assert os.environ.get('OPENROUTER_API_KEY'), 'OPENROUTER_API_KEY ausente'
        from browser_use.llm.messages import UserMessage

        async def verificar_sdk():
            def responder(request):
                corpo = json.loads(request.content)
                assert corpo['usage'] == {'include': True}
                assert corpo['max_tokens'] == MAX_TOKENS_CUA
                return httpx.Response(200, json={
                    'id': 'check-local', 'object': 'chat.completion', 'created': 0, 'model': MODEL,
                    'choices': [{'index': 0, 'finish_reason': 'stop', 'message': {
                        'role': 'assistant', 'content': '{"passou":true,"evidencia":"teste local"}'}}],
                    'usage': {'prompt_tokens': 2, 'completion_tokens': 3, 'total_tokens': 5, 'cost': 0.1},
                })
            async with httpx.AsyncClient(transport=httpx.MockTransport(responder)) as client:
                llm = ChatOpenRouter(model=MODEL, api_key='check-local', http_client=client,
                    max_retries=0, extra_body=PARAMETROS_LLM)
                resposta = await llm.ainvoke([UserMessage(content='teste local')], output_format=VeredictoCriterio)
                assert resposta.completion.passou
                assert resposta.usage.total_tokens == 5

        import tempfile
        with tempfile.TemporaryDirectory() as pasta:
            foto = Path(pasta) / 'foto.png'
            foto.write_bytes(b'local-test')
            mensagens = judge_completo(task='teste local', final_result='teste local',
                agent_steps=['passo'], screenshot_paths=[str(foto)] * 12, max_images=10)
            assert len(mensagens[1].content) == 13, 'O judge deve receber todas as 12 imagens e o texto'
        asyncio.run(verificar_sdk())
        print('Checks locais OK; nenhuma chamada ao modelo.')
    else:
        asyncio.run(main())
