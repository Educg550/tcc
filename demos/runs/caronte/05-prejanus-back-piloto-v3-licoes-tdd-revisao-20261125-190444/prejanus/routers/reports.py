import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask

from prejanus import reports_gen
from prejanus.db import get_db
from prejanus.deps import require_admin
from prejanus.models import Edict, User

router = APIRouter(tags=["edicts"])


@router.post("/edicts/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: int,
    background_tasks: BackgroundTasks,
    mode: str = "plain_text",
    sections: dict | None = None,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await db.get(Edict, edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    options = sections or {}
    if mode == "pdf":
        job_id = uuid.uuid4().hex
        background_tasks.add_task(reports_gen.generate_pdf, job_id, edict_id, options)
        return {"job_id": job_id, "status": "processing"}
    interactors = await reports_gen._interactors(db, edict_id)
    return interactors


@router.post("/edicts/{edict_id}/pairing-biddings")
async def pairing_biddings(
    edict_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await db.get(Edict, edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    job_id = uuid.uuid4().hex
    background_tasks.add_task(reports_gen.generate_csv, job_id, edict_id)
    return {"job_id": job_id, "status": "processing"}


def _safe_job(job_id: str) -> str | None:
    if not job_id or "/" in job_id or ".." in job_id:
        return None
    return job_id


@router.get("/edicts/download_pdf/{job_id}")
async def download_pdf(job_id: str):
    job = _safe_job(job_id)
    path = reports_gen._pdf_path(job) if job else None
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return FileResponse(
        path,
        media_type="application/pdf",
        headers={"content-disposition": f'inline; filename="report_{job}.pdf"'},
        background=BackgroundTask(os.remove, path),
    )


@router.get("/edicts/download_csv/{job_id}")
async def download_csv(job_id: str):
    job = _safe_job(job_id)
    path = reports_gen._csv_path(job) if job else None
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return FileResponse(
        path,
        media_type="text/csv",
        headers={"content-disposition": f'inline; filename="report_{job}.csv"'},
        background=BackgroundTask(os.remove, path),
    )
