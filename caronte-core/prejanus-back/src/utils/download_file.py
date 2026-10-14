from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

PDF_STORAGE = Path("/tmp")

def file_iterator(path: Path, chunk_size=8192):
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            yield chunk
    try:
        path.unlink()
    except FileNotFoundError:
        pass

async def download_generate_pdf_file(job_id: str):
    pdf_path = PDF_STORAGE / f"{job_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not ready yet")

    return StreamingResponse(
        file_iterator(pdf_path), 
        media_type="application/pdf", 
        headers={"Content-Disposition": f'inline; filename="{job_id}.pdf"'}
        )

async def download_generate_csv_file(job_id: str):
    csv_path = PDF_STORAGE / f"{job_id}.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="CSV not ready yet")

    return StreamingResponse(
        file_iterator(csv_path), 
        media_type="text/csv", 
        headers={"Content-Disposition": f'inline; filename="{job_id}.csv"'}
        )
