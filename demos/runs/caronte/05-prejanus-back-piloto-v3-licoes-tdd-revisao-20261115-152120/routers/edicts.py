import threading
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_current_user, get_db, get_forms_db, require_admin
from models import (
    Comment,
    Edict,
    EdictFormMapping,
    EdictPhase,
    Favorite,
    Label,
    PrivateNote,
    Submission,
    User,
    UserEdictSlot,
)
from services import forms_db, jobs, reports
from services.mapping import flatten_mapping
from services.submissions import (
    build_submission_item,
    load_edict_submissions,
)

router = APIRouter(prefix="/edicts", tags=["edicts"])

PHASE_DATES = {
    "inscricoes": "date_application",
    "homologacao": "date_evaluation",
    "avaliacao": "date_verification",
    "encerrado": "date_closed",
}
FORMS_PHASE = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}
PHASE_ORDER = ["inscricoes", "homologacao", "avaliacao", "encerrado"]


async def _get_edict(db: AsyncSession, edict_id: int) -> Edict:
    edict = await db.get(Edict, edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    return edict


def _check_dates(dates: dict) -> None:
    values = [dates[k] for k in
              ("date_application", "date_evaluation", "date_verification",
               "date_closed")]
    if not all(values[i] < values[i + 1] for i in range(3)):
        raise HTTPException(
            status_code=422,
            detail="As datas devem estar em ordem cronológica estrita: "
                   "inscricoes < homologacao < avaliacao < encerrado",
        )


def _edict_list_item(e: Edict) -> dict:
    return {
        "id": e.id,
        "title": e.title,
        "year": e.year,
        "semester": e.semester,
        "edict_type": e.type,
        "is_open": e.is_open,
    }


@router.get("")
async def get_all_edicts(
    type: str | None = None,
    is_open: bool | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Edict).order_by(Edict.closed_date.desc(), Edict.id.desc())
    if type is not None:
        stmt = stmt.where(Edict.type == type)
    if is_open is not None:
        stmt = stmt.where(Edict.is_open == is_open)
    edicts = (await db.execute(stmt)).scalars().all()
    return [_edict_list_item(e) for e in edicts]


async def _edict_detail(db: AsyncSession, edict: Edict, user: User) -> dict:
    phases = (
        (
            await db.execute(
                select(EdictPhase)
                .where(EdictPhase.edict_id == edict.id)
                .order_by(EdictPhase.id)
            )
        )
        .scalars()
        .all()
    )
    slot = (
        await db.execute(
            select(UserEdictSlot).where(
                UserEdictSlot.user_id == user.id,
                UserEdictSlot.edict_id == edict.id,
            )
        )
    ).scalars().first()
    return {
        "id": edict.id,
        "title": edict.title,
        "candidate_form_id": edict.candidate_forms,
        "recommender_form_id": edict.recommenders_forms,
        "accept_form_id": edict.accept_forms,
        "description": edict.description,
        "closed_date": edict.closed_date.isoformat() if edict.closed_date else None,
        "created_at": edict.created_at,
        "year": edict.year,
        "semester": edict.semester,
        "type": edict.type,
        "is_open": edict.is_open,
        "updated_at": edict.updated_at,
        "phase": edict.phase,
        "phases": [
            {
                "id": p.id,
                "closed_date": p.closed_date.isoformat() if p.closed_date else None,
                "phase": p.phase,
            }
            for p in phases
        ],
        "slots": str(slot.slots) if slot and slot.slots is not None else "0",
    }


@router.get("/{edict_id}")
async def get_edict(
    edict_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    edict = await _get_edict(db, edict_id)
    return await _edict_detail(db, edict, user)


class InsertEdictSchema(BaseModel):
    title: str
    description: str | None = None
    year: int
    semester: int
    edict_type: str
    is_open: bool
    candidate_forms: int
    recommenders_forms: int
    date_application: datetime
    date_evaluation: datetime
    date_verification: datetime
    date_closed: datetime


@router.post("")
async def create_edict(
    body: InsertEdictSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    _check_dates(body.model_dump())
    edict = Edict(
        title=body.title,
        description=body.description,
        candidate_forms=str(body.candidate_forms),
        recommenders_forms=str(body.recommenders_forms),
        closed_date=body.date_closed.date(),
        year=body.year,
        semester=body.semester,
        type=body.edict_type,
        phase="inscricoes",
        is_open=body.is_open,
        user_id=user.id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(edict)
    await db.flush()
    for phase in PHASE_ORDER:
        db.add(
            EdictPhase(
                edict_id=edict.id,
                phase=phase,
                closed_date=getattr(body, PHASE_DATES[phase]).date(),
            )
        )
    await db.commit()
    return {
        "title": edict.title,
        "description": edict.description,
        "year": edict.year,
        "semester": edict.semester,
        "edict_type": edict.type,
        "is_open": edict.is_open,
        "candidate_forms": body.candidate_forms,
        "recommenders_forms": body.recommenders_forms,
        "date_application": body.date_application,
        "date_evaluation": body.date_evaluation,
        "date_verification": body.date_verification,
        "date_closed": body.date_closed,
        "id": edict.id,
        "closed_date": body.date_closed,
    }


class EditEdictSchema(BaseModel):
    title: str
    description: str | None = None
    year: str
    semester: str
    edict_type: str
    date_application: datetime
    date_evaluation: datetime
    date_verification: datetime
    date_closed: datetime


@router.post("/{edict_id}/edit")
async def edit_edict(
    edict_id: int,
    body: EditEdictSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    edict = await _get_edict(db, edict_id)
    _check_dates(body.model_dump())
    try:
        year = int(body.year)
        semester = int(body.semester)
    except ValueError:
        raise HTTPException(status_code=422, detail="Ano e semestre inválidos")
    edict.title = body.title
    edict.description = body.description
    edict.year = year
    edict.semester = semester
    edict.type = body.edict_type
    edict.closed_date = body.date_closed.date()
    edict.updated_at = datetime.now()
    phases = (
        await db.execute(select(EdictPhase).where(EdictPhase.edict_id == edict.id))
    ).scalars().all()
    for phase in phases:
        phase.closed_date = getattr(body, PHASE_DATES[phase.phase]).date()
    await db.commit()
    return {
        "title": body.title,
        "description": body.description,
        "year": body.year,
        "semester": body.semester,
        "edict_type": body.edict_type,
        "date_application": body.date_application,
        "date_evaluation": body.date_evaluation,
        "date_verification": body.date_verification,
        "date_closed": body.date_closed,
    }


class EditEdictDateSchema(BaseModel):
    closed_date: date


@router.post("/{edict_id}/edit-date")
async def edit_edict_date(
    edict_id: int,
    body: EditEdictDateSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    edict = await _get_edict(db, edict_id)
    edict.closed_date = body.closed_date
    edict.updated_at = datetime.now()
    phases = (
        await db.execute(
            select(EdictPhase).where(
                EdictPhase.edict_id == edict.id, EdictPhase.phase == "encerrado"
            )
        )
    ).scalars().all()
    for phase in phases:
        phase.closed_date = body.closed_date
    await db.commit()
    return {"closed_date": body.closed_date.isoformat()}


class AdvancePhaseEdictSchema(BaseModel):
    id: int


@router.post("/{edict_id}/advance-phase")
async def advance_phase(
    edict_id: int,
    body: AdvancePhaseEdictSchema,
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
    user: User = Depends(require_admin),
):
    edict = await _get_edict(db, edict_id)
    phase = (
        await db.execute(
            select(EdictPhase).where(
                EdictPhase.id == body.id, EdictPhase.edict_id == edict.id
            )
        )
    ).scalars().first()
    if phase is None:
        raise HTTPException(status_code=404, detail="Fase não encontrada")
    edict.phase = phase.phase
    edict.updated_at = datetime.now()
    await db.commit()
    if edict.candidate_forms:
        await forms_db.change_form_phase(
            fdb, int(edict.candidate_forms), FORMS_PHASE[phase.phase]
        )
    return {"id": phase.id, "label": phase.phase}


class CloseEdictSchema(BaseModel):
    confirmation_deadline: date
    send_approval_letter: bool


@router.patch("/{edict_id}/close")
async def close_edict(
    edict_id: int,
    body: CloseEdictSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    edict = await _get_edict(db, edict_id)
    if not edict.is_open:
        raise HTTPException(status_code=409, detail="Edital já encerrado")
    edict.is_open = False
    edict.updated_at = datetime.now()
    await db.commit()
    return {"message": "Edital encerrado com sucesso"}


@router.delete("/{edict_id}/remove")
async def remove_edict(
    edict_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    edict = await _get_edict(db, edict_id)
    await db.delete(edict)
    await db.commit()
    return {"message": "Edital removido com sucesso"}


# ---------------------------------------------------------------- mapeamentos

FORM_TYPE_BY_PATH = {"candidates": "candidate", "recommenders": "recommender"}


def _mapping_dict(m: EdictFormMapping) -> dict:
    return {
        "id": m.id,
        "edict_id": m.edict_id,
        "form_type": m.form_type,
        "form_id": m.form_id,
        "user_id": m.user_id,
        "form_version": m.form_version,
        "version": m.form_version,
        "mapping": m.mapping,
        "is_active": m.is_active,
        "created_at": m.created_at,
    }


async def _validate_tree(fdb: AsyncSession, form_id: int, version: int, tree) -> None:
    leaves = [leaf for _, leaf in flatten_mapping(tree) if leaf is not None]
    res = await fdb.execute(
        text("select id from form_section where form_id = :fid"),
        {"fid": form_id},
    )
    section_ids = {r[0] for r in res.fetchall()}
    res = await fdb.execute(
        text(
            "select id, section_id from form_field where form_id = :fid "
            "and (version = :v or (:v = 1 and version is null))"
        ),
        {"fid": form_id, "v": version},
    )
    version_fields = {r[0]: r[1] for r in res.fetchall()}
    res = await fdb.execute(
        text("select id, section_id from form_field where form_id = :fid"),
        {"fid": form_id},
    )
    # fallback original: sem campos nesta versão, considera todos do formulário
    all_fields = version_fields or {r[0]: r[1] for r in res.fetchall()}
    for leaf in leaves:
        if leaf["section"] not in section_ids:
            raise HTTPException(status_code=422, detail="Seção inválida no mapeamento")
        if leaf["field"] not in all_fields:
            raise HTTPException(status_code=422, detail="Campo inválido no mapeamento")
        if all_fields[leaf["field"]] != leaf["section"]:
            raise HTTPException(
                status_code=422, detail="Campo não pertence à seção informada"
            )


async def _mapping_form_id(edict: Edict, form_type: str) -> int:
    value = edict.candidate_forms if form_type == "candidate" else edict.recommenders_forms
    if not value:
        raise HTTPException(
            status_code=404,
            detail="Edital sem formulário associado a este tipo",
        )
    return int(value)


@router.post("/{edict_id}/{tipo}/mappings/versions/{version}/")
async def create_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    tree: dict,
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
    user: User = Depends(require_admin),
):
    if tipo not in FORM_TYPE_BY_PATH:
        raise HTTPException(status_code=404, detail="Tipo de mapeamento inválido")
    form_type = FORM_TYPE_BY_PATH[tipo]
    edict = await _get_edict(db, edict_id)
    form_id = await _mapping_form_id(edict, form_type)
    await _validate_tree(fdb, form_id, version, tree)
    existing = (
        await db.execute(
            select(EdictFormMapping).where(
                EdictFormMapping.edict_id == edict.id,
                EdictFormMapping.form_type == form_type,
                EdictFormMapping.form_version == version,
            )
        )
    ).scalars().first()
    if existing is not None:
        raise HTTPException(
            status_code=409, detail="Já existe mapeamento para esta versão"
        )
    mapping = EdictFormMapping(
        edict_id=edict.id,
        form_type=form_type,
        mapping=tree,
        is_active=True,
        form_id=str(form_id),
        user_id=user.id,
        form_version=version,
    )
    db.add(mapping)
    await db.commit()
    return _mapping_dict(mapping)


@router.get("/{edict_id}/{tipo}/mappings")
async def get_mappings(
    edict_id: int,
    tipo: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if tipo not in FORM_TYPE_BY_PATH:
        raise HTTPException(status_code=404, detail="Tipo de mapeamento inválido")
    edict = await _get_edict(db, edict_id)
    mappings = (
        await db.execute(
            select(EdictFormMapping)
            .where(
                EdictFormMapping.edict_id == edict.id,
                EdictFormMapping.form_type == FORM_TYPE_BY_PATH[tipo],
            )
            .order_by(EdictFormMapping.id)
        )
    ).scalars().all()
    return [_mapping_dict(m) for m in mappings]


async def _find_mapping(db, edict_id, form_type, version, mapping_id):
    mapping = (
        await db.execute(
            select(EdictFormMapping).where(
                EdictFormMapping.id == mapping_id,
                EdictFormMapping.edict_id == edict_id,
                EdictFormMapping.form_type == form_type,
                EdictFormMapping.form_version == version,
            )
        )
    ).scalars().first()
    if mapping is None:
        raise HTTPException(status_code=404, detail="Mapeamento não encontrado")
    return mapping


@router.put("/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
async def update_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    mapping_id: int,
    tree: dict,
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
    user: User = Depends(require_admin),
):
    if tipo not in FORM_TYPE_BY_PATH:
        raise HTTPException(status_code=404, detail="Tipo de mapeamento inválido")
    form_type = FORM_TYPE_BY_PATH[tipo]
    edict = await _get_edict(db, edict_id)
    mapping = await _find_mapping(db, edict_id, form_type, version, mapping_id)
    form_id = await _mapping_form_id(edict, form_type)
    await _validate_tree(fdb, form_id, version, tree)
    mapping.mapping = tree
    await db.commit()
    return _mapping_dict(mapping)


@router.delete("/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
async def delete_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    mapping_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    if tipo not in FORM_TYPE_BY_PATH:
        raise HTTPException(status_code=404, detail="Tipo de mapeamento inválido")
    form_type = FORM_TYPE_BY_PATH[tipo]
    await _get_edict(db, edict_id)
    mapping = await _find_mapping(db, edict_id, form_type, version, mapping_id)
    await db.delete(mapping)
    await db.commit()
    return {"message": "Mapping deleted successfully"}


@router.get("/{edict_id}/{tipo}/forms/versions/unmapped")
async def get_unmapped_versions(
    edict_id: int,
    tipo: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if tipo not in FORM_TYPE_BY_PATH:
        raise HTTPException(status_code=404, detail="Tipo de mapeamento inválido")
    form_type = FORM_TYPE_BY_PATH[tipo]
    edict = await _get_edict(db, edict_id)
    column = (
        Submission.candidate_form_version
        if form_type == "candidate"
        else Submission.recommender_form_version
    )
    versions = {
        r[0]
        for r in (
            await db.execute(
                select(column)
                .where(Submission.edict_id == edict.id)
                .distinct()
            )
        ).fetchall()
    }
    mapped = {
        r[0]
        for r in (
            await db.execute(
                select(EdictFormMapping.form_version).where(
                    EdictFormMapping.edict_id == edict.id,
                    EdictFormMapping.form_type == form_type,
                )
            )
        ).fetchall()
    }
    return sorted(v for v in versions if v not in mapped)


# -------------------------------------------------------------------- relatórios

class SectionsDocument(BaseModel):
    list_of_advisors: bool | None = False
    relation: bool | None = False
    approved: bool | None = False
    refused: bool | None = False
    underreview: bool | None = False
    general_statistics: bool | None = False
    show_emails: bool | None = False


async def _interactors(db: AsyncSession, edict: Edict) -> list[User]:
    user_ids: set[int] = set()
    for model in (Comment, Favorite, Label, PrivateNote):
        rows = (
            await db.execute(
                select(model.user_id)
                .join(Submission, Submission.id == model.submission_id)
                .where(Submission.edict_id == edict.id)
                .distinct()
            )
        ).fetchall()
        user_ids.update(r[0] for r in rows)
    users = []
    for uid in sorted(user_ids):
        u = await db.get(User, uid)
        if u:
            users.append(u)
    return users


@router.post("/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: int,
    mode: str = "plain_text",
    document: SectionsDocument | None = None,
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
    user: User = Depends(require_admin),
):
    edict = await _get_edict(db, edict_id)
    document = document or SectionsDocument()
    interactors = await _interactors(db, edict)
    if mode != "pdf":
        return [
            {"id": u.id, "name": u.name, "email": u.email} for u in interactors
        ]

    loaded = await load_edict_submissions(db, fdb, edict)
    items = []
    for sub, resp, data in loaded:
        items.append(
            await build_submission_item(db, fdb, edict, sub, resp, data, user)
        )

    finished = in_progress = 0
    if edict.candidate_forms:
        res = await fdb.execute(
            text(
                "select count(*) filter (where submitted_at is not null), "
                "count(*) filter (where submitted_at is null) "
                "from form_response where form_id = :fid"
            ),
            {"fid": int(edict.candidate_forms)},
        )
        finished, in_progress = res.fetchone()

    by_status: dict[str, list] = {}
    for item in items:
        by_status.setdefault(item["stats"], []).append(item)

    advisors = []
    slots_rows = (
        await db.execute(
            select(UserEdictSlot).where(UserEdictSlot.edict_id == edict.id)
        )
    ).scalars().all()
    for slot in slots_rows:
        u = await db.get(User, slot.user_id)
        if u:
            advisors.append(
                {"name": u.name, "email": u.email,
                 "slots": slot.slots if slot.slots is not None else 0}
            )

    document_data = {
        "title": edict.title,
        "year": edict.year,
        "semester": edict.semester,
        "edict_type": edict.type,
        "options": {
            "general_statistics": document.general_statistics,
            "list_of_advisors": document.list_of_advisors,
            "relation": document.relation,
            "approved": document.approved,
            "refused": document.refused,
            "underreview": document.underreview,
            "show_emails": document.show_emails,
        },
        "statistics": {
            "finished": finished,
            "in_progress": in_progress,
            "by_status": {k: len(v) for k, v in by_status.items()},
        },
        "advisors": advisors,
        "approved": by_status.get("approved", []),
        "by_status": by_status,
        "emails": [i["email"] for i in items if i["email"]],
    }
    job_id = jobs.new_job_id()
    path = jobs.job_path(job_id, "pdf")
    threading.Thread(
        target=reports.render_pdf, args=(path, document_data), daemon=True
    ).start()
    return {"job_id": job_id, "status": "processing"}


@router.post("/{edict_id}/pairing-biddings")
async def pairing_biddings(
    edict_id: int,
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
    user: User = Depends(require_admin),
):
    edict = await _get_edict(db, edict_id)
    loaded = await load_edict_submissions(db, fdb, edict)

    bidding_labels = (
        await db.execute(
            select(Label)
            .join(Submission, Submission.id == Label.submission_id)
            .where(Submission.edict_id == edict.id, Label.context_type == "bidding")
        )
    ).scalars().all()
    teacher_ids = sorted({l.user_id for l in bidding_labels})
    teachers = []
    for tid in teacher_ids:
        u = await db.get(User, tid)
        if u:
            slot = (
                await db.execute(
                    select(UserEdictSlot).where(
                        UserEdictSlot.user_id == tid,
                        UserEdictSlot.edict_id == edict.id,
                    )
                )
            ).scalars().first()
            teachers.append(
                (u, slot.slots if slot and slot.slots is not None else 0)
            )

    rows = [["#"] + [u.email for u, _ in teachers]]
    rows.append(["slots"] + [str(s) for _, s in teachers])
    for sub, resp, _data in loaded:
        values = ["" for _ in teachers]
        for lab in bidding_labels:
            if lab.submission_id != sub.id:
                continue
            for idx, (u, _s) in enumerate(teachers):
                if u.id == lab.user_id:
                    values[idx] = lab.label
        rows.append([resp["email"] or ""] + values)

    job_id = jobs.new_job_id()
    path = jobs.job_path(job_id, "csv")
    threading.Thread(
        target=reports.render_csv, args=(path, rows), daemon=True
    ).start()
    return {"job_id": job_id, "status": "processing"}


@router.get("/download_pdf/{job_id}")
async def download_pdf(job_id: str):
    content = jobs.read_and_delete(job_id, "pdf")
    if content is None:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{job_id}.pdf"',
        },
    )


@router.get("/download_csv/{job_id}")
async def download_csv(job_id: str):
    content = jobs.read_and_delete(job_id, "csv")
    if content is None:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'inline; filename="{job_id}.csv"',
        },
    )


# ----------------------------------------------------------------------- vagas

class SlotsSchema(BaseModel):
    amount: str


@router.post("/{edict_id}/slots")
async def set_user_slots(
    edict_id: int,
    body: SlotsSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_edict(db, edict_id)
    raw = (body.amount or "").strip()
    if raw == "":
        amount = 0
    else:
        try:
            amount = int(raw)
        except ValueError:
            raise HTTPException(status_code=422, detail="Quantidade inválida")
        if amount < 0:
            amount = 0
    slot = (
        await db.execute(
            select(UserEdictSlot).where(
                UserEdictSlot.user_id == user.id,
                UserEdictSlot.edict_id == edict_id,
            )
        )
    ).scalars().first()
    if slot is None:
        slot = UserEdictSlot(user_id=user.id, edict_id=edict_id, slots=amount)
        db.add(slot)
    else:
        slot.slots = amount
    await db.commit()
    return {"amount": str(amount)}


# ------------------------------------------------------------------ inscrições

@router.get("/{edict_id}/submissions")
async def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
    user: User = Depends(get_current_user),
):
    edict = await _get_edict(db, edict_id)
    loaded = await load_edict_submissions(db, fdb, edict)
    favorites = {
        r[0]
        for r in (
            await db.execute(
                select(Favorite.submission_id).where(Favorite.user_id == user.id)
            )
        ).fetchall()
    }
    items = []
    for sub, resp, data in loaded:
        if stats is not None and sub.stats != stats:
            continue
        if only_favorites and sub.id not in favorites:
            continue
        items.append(
            await build_submission_item(db, fdb, edict, sub, resp, data, user)
        )
    return {"submissions": items}
