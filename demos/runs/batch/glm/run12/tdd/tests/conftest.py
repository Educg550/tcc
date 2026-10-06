import sys
from pathlib import Path

# Garante que a raiz do projeto (onde vivem app.py, index.html, style.css,
# app.js e assets/) fique importável, independentemente de onde o pytest é
# chamado.
RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
