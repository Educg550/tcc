from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from fastapi.responses import Response

from auth import require_admin
from services import reports_service as reports
from services.submissions_service import get_edict

router = APIRouter(tags=["edicts"])


@router.post("/edicts/{edict_id}/interactors_list")
def interactors_list(
    edict_id: int,
    background: BackgroundTasks,
    mode: str = "plain_text",
    payload: dict = Body(default={}),
    user=Depends(require_admin),
):
    if not get_edict(edict_id):
        raise HTTPException(status_code=404, detail="Edict not found")
    if mode == "pdf":
        job_id, path = reports.new_job("pdf")
        background.add_task(reports.generate_pdf, job_id, path, edict_id, payload)
        return {"job_id": job_id, "status": "processing"}
    return reports._interactors(edict_id)


@router.post("/edicts/{edict_id}/pairing-biddings")
def pairing_biddings(
    edict_id: int,
    background: BackgroundTasks,
    user=Depends(require_admin),
):
    if not get_edict(edict_id):
        raise HTTPException(status_code=404, detail="Edict not found")
    job_id, path = reports.new_job("csv")
    background.add_task(reports.generate_csv, job_id, path, edict_id)
    return {"job_id": job_id, "status": "processing"}


@router.get("/edicts/download_pdf/{job_id}")
def download_pdf(job_id: str):
    content = reports.read_and_remove(job_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{job_id}.pdf"'},
    )


@router.get("/edicts/download_csv/{job_id}")
def download_csv(job_id: str):
    content = reports.read_and_remove(job_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'inline; filename="{job_id}.csv"'},
    )
