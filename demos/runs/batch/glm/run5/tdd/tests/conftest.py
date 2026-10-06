import sys
from pathlib import Path

# O harness inicia a aplicação com `uvicorn app:app` a partir da raiz do projeto;
# garantir que `from app import app` também funcione quando o pytest roda.
RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
