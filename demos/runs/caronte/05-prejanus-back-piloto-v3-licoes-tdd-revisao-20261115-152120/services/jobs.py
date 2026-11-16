import os
import uuid

TMP_DIR = "/tmp"


def new_job_id() -> str:
    return uuid.uuid4().hex


def job_path(job_id: str, ext: str) -> str:
    safe = "".join(c for c in job_id if c.isalnum() or c in "-_")
    return os.path.join(TMP_DIR, f"{safe}.{ext}")


def read_and_delete(job_id: str, ext: str) -> bytes | None:
    path = job_path(job_id, ext)
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as f:
        content = f.read()
    os.remove(path)
    return content
