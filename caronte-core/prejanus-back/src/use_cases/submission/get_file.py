import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from src.infra.database.models.submission import Submission
from src.use_cases.dtos import UserDTO
from src.use_cases.submission.exceptions import SubmissionNotFound
from werkzeug.utils import secure_filename

import io
from fpdf import FPDF
from pypdf import PdfReader, PdfWriter
from datetime import datetime

def add_watermark(path_pdf, text):
    # removido para evitar timeouts
    # pensar em outrao slucao
    return io.BytesIO(open(path_pdf, "rb").read())
    try:
        reader = PdfReader(path_pdf)
        if reader.is_encrypted:
            return io.BytesIO(open(path_pdf, "rb").read())
        writer = PdfWriter()

        mark_pdf = io.BytesIO()
        pdf_mark = FPDF()
        pdf_mark.add_page()
        pdf_mark.set_font("Helvetica", "B", 12)
        pdf_mark.set_text_color(200, 200, 200)
        
        x = 5
        y = pdf_mark.h - 1.5
        pdf_mark.text(x, y, text)

        pdf_mark.output(mark_pdf)
        mark_pdf.seek(0)

        marca_reader = PdfReader(mark_pdf)
        mark_page = marca_reader.pages[0]

        for page in reader.pages:
            page.merge_page(mark_page)
            writer.add_page(page)

        pdf_final = io.BytesIO()
        writer.write(pdf_final)
        pdf_final.seek(0)
        return pdf_final
    except Exception:
        return io.BytesIO(open(path_pdf, "rb").read())

async def get_file_by_submission(
        submission_id: int, 
        label: str,
        filename: str, 
        session: AsyncSession, 
        session_forms: AsyncSession,
        auth_user: UserDTO
    ):
    # conferir se nome de arquivo é válido
    stmt = (
        select(Submission)
        .where(Submission.id == submission_id)
    )
    result = await session.execute(stmt)
    submission = result.scalars().one_or_none()
    
    if submission is None:
        raise SubmissionNotFound(submission_id)
    
    query = text("""
        select * from get_submissions_by_id(
            cast(:p_response_id as int),
            cast(:p_lang as text)
        )
    """)
    params = {
        "p_response_id": int(submission.candidate_form_id),
        "p_lang": "pt" 
    }
    result = await session_forms.execute(
        query,
        params
    )

    candidates_forms_submissions = dict(result.fetchone()._mapping)

    dict_responses = {k: v for d in candidates_forms_submissions['responses'] for k, v in d.items()}
    field = dict_responses.get(label, None)

    if field.get("value") != filename:
        raise

    safe_name = secure_filename(field.get("value"))
    url = f"/shared/uploads/{safe_name}"

    if os.path.exists(url):
        pdf_marked = add_watermark(url, f'{auth_user.email} - {datetime.now()}')

        return pdf_marked
    else:
        raise
