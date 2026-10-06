import re
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import quote

from fastapi import Body, FastAPI
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse

BASE_DIR = Path(__file__).parent.resolve()
ZIP_PATH = BASE_DIR / "dist.zip"
app = FastAPI(title="Quantum Codecs")

DATA_DIR = BASE_DIR / "data"
DEPLOYMENT_ROOT = "/opt/quantumcodecs/"

FILES_MANIFEST = [
    "run_qc.py",
    "qc_api.py",
    "qc_core/__init__.py",
    "qc_core/audio/__init__.py",
    "qc_core/audio/pcm.py",
    "qc_core/audio/quantization.py",
    "qc_core/codecs/__init__.py",
    "qc_core/codecs/delta.py",
    "qc_core/codecs/huffman.py",
    "qc_core/codecs/rle.py",
    "qc_core/packets.py",
    "qc_core/visual/__init__.py",
    "qc_core/visual/image.py",
    "qc_core/visual/video.py",
]

SERVICE_FILE_TEMPLATE = """[Unit]
Description=Quantum Codecs media API
After=network.target

[Service]
WorkingDirectory={root}
ExecStart={python} run_qc.py --workdir {root}/work
Restart=always

[Install]
WantedBy=multi-user.target
"""


def zip_file_content(path: str) -> str:
    with zipfile.ZipFile(ZIP_PATH) as archive:
        return archive.read(path).decode("utf-8")


def check_deployment(content: str) -> bool:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return False
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    names.update(
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
    )
    return not (names & {"eval", "exec", "__import__"})


class NativeQuery(BaseModel):
    action: str = Field(..., min_length=1)
    target: str
    content: str = ""
    params: list[str] = []


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/run")
def run_operation(request: NativeQuery) -> dict[str, object]:
    action = request.action
    target = request.target
    content = request.content
    params = request.params
    path = (DATA_DIR / target).resolve()
    try:
        path.relative_to(DATA_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid target")
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if action == "read":
        return {"content": path.read_text(encoding="utf-8")}
    elif action == "write":
        path.write_text(content, encoding="utf-8")
        return {"status": "ok"}
    elif action == "scan":
        forbidden = ["eval(", "exec(", "__import__("]
        text = path.read_text(encoding="utf-8")
        findings = [word for word in forbidden if word in text]
        return {"findings": findings}
    elif action == "checksum":
        data = path.read_bytes()
        return {"sha256": hashlib.sha256(data).hexdigest()}
    else:
        raise HTTPException(status_code=400, detail="Unsupported action")


@app.get("/api/tree")
def get_tree() -> dict[str, object]:
    if not DATA_DIR.exists():
        return {"entries": []}
    entries = []
    for item in DATA_DIR.rglob("*"):
        rel = item.relative_to(DATA_DIR).as_posix()
        if item.is_dir():
            entries.append({"path": rel, "type": "directory"})
        else:
            size = item.stat().st_size
            entries.append({"path": rel, "type": "file", "size": size})
    return {"entries": sorted(entries, key=lambda entry: entry["path"])}


@app.get("/api/report")
def get_report() -> dict[str, object]:
    if not DATA_DIR.exists():
        return {"files": [], "total_size": 0}
    files = [item for item in DATA_DIR.rglob("*") if item.is_file()]
    total_size = sum(item.stat().st_size for item in files)
    return {
        "files": [item.relative_to(DATA_DIR).as_posix() for item in sorted(files)],
        "total_size": total_size,
    }


@app.get("/api/download/{rel_path}")
def download_file(rel_path: str):
    path = (DATA_DIR / rel_path).resolve()
    try:
        path.relative_to(DATA_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid target")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=path.name)


@app.get("/files")
def list_files() -> dict[str, object]:
    entries = []
    for path in FILES_MANIFEST:
        content = zip_file_content(path)
        entries.append({
            "path": path,
            "size": len(content.encode("utf-8")),
            "lines": content.count("\n") + 1,
        })
    return {"entries": entries}


@app.get("/files/{path:path}")
def read_file(path: str):
    if path not in FILES_MANIFEST:
        raise HTTPException(status_code=404, detail="File not found")
    return PlainTextResponse(zip_file_content(path))


@app.get("/deploy/tarball")
def get_tarball() -> FileResponse:
    tar_path = BASE_DIR / "qc.tar.gz"
    with tarfile.open(tar_path, "w:gz") as archive:
        for path in FILES_MANIFEST:
            archive.add(path, arcname=path)
    return FileResponse(tar_path, filename="qc.tar.gz")


@app.get("/deploy/zip")
def get_zip() -> FileResponse:
    return FileResponse(ZIP_PATH, filename="dist.zip")


@app.get("/deploy/bundle")
def get_bundle() -> dict[str, object]:
    temp = BASE_DIR / ".bundle_build"
    if temp.exists():
        shutil.rmtree(temp)
    root = temp / "bundle"
    root.mkdir(parents=True)
    for path in FILES_MANIFEST:
        dest = root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(zip_file_content(path), encoding="utf-8")
    service_text = SERVICE_FILE_TEMPLATE.format(
        root=DEPLOYMENT_ROOT,
        python=sys.executable or "/usr/bin/python3",
    )
    (root / "qc.service").write_text(service_text, encoding="utf-8")
    return {
        "root": str(root),
        "service": service_text,
        "files": FILES_MANIFEST,
    }
