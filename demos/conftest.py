import os
import sys
from pathlib import Path

# Adicionar src de qualquer subprojeto em output/ ao path
output_dir = Path(__file__).parent / "output"
if output_dir.exists():
    for subproject in output_dir.iterdir():
        if subproject.is_dir():
            src_dir = subproject / "src"
            if src_dir.exists():
                # Adicionar ao sys.path para imports diretos
                if str(src_dir) not in sys.path:
                    sys.path.insert(0, str(src_dir))
                # Também adicionar ao PYTHONPATH para subprocess.run
                pythonpath = os.environ.get("PYTHONPATH", "")
                if str(src_dir) not in pythonpath:
                    os.environ["PYTHONPATH"] = f"{src_dir}:{pythonpath}".rstrip(":")
