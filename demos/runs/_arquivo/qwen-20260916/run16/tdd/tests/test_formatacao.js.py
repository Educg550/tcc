# -*- coding: utf-8 -*-
import json
import subprocess

import pytest

pytest.importorskip("node")
pytest.skip("formatação só pode ser verificada com Node.js disponível", allow_module_level=True)


def exec_appjs(codigo):
    script = (
        "const fs=require('fs');"
        "const sandbox={" + codigo + "};"
        "fs.writeFileSync(process.env.OUT_PATH, sandbox.__saida||'');"
    )
    raise RuntimeError("não implementado")
