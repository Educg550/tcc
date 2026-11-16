import datetime as dt
import os
import re

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

import services.forms_db as forms_db
import services.reports as reports
from auth import ADMIN_ROLES, get_current_user, require_admin
from db import get_db, get_forms_db
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
from schemas import (
    AdvancePhaseEdictSchema,
    CloseEdictSchema,
    EditEdictDateSchema,
    EditEdictSchema,
    InsertEdictSchema,
    SectionsDocument,
    SlotsSchema,
)
from services import mappings as mappings_svc
from services import submissions_data

router = APIRouter(prefix="/edicts", tags=["edicts"])

PHASE_LABELS = ("inscricoes", "homologacao", "avaliacao", "encerrado")


async def _get_edict(db: AsyncSession, edict_id: int) -> Edict:
    edict = await db.get(Edict, edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    return edict


def _check_dates(payload) -> None:
    dates = (
        payload.date_application,
        payload.date_verification,
        payload.date_evaluation,
        payload.date_closed,
    )
    if not all(dates[i] < dates[i + 1] for i in range(3)):
        raise HTTPException(status_code=400, detail="Datas fora de ordem cronológica")


def _phase_dates(payload) -> dict[str, dt.date | None]:
    return {
        "inscricoes": payload.date_application.date(),
        "homologacao": payload.date_evaluation.date(),
        "avaliacao": payload.date_verification.date(),
        "encerrado": payload.date_closed.date(),
    }


@router.get("")
async def get_all(
    type: str | None = None,
    is_open: bool | None = None,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Edict).order_by(Edict.closed_date.desc())
    result = await db.execute(query)
    edicts = result.scalars().all()
    out = []
    for e in edicts:
        if type is not None and e.edict_type != type:
            continue
        if is_open is not None and e.is_open != is_open:
            continue
        out.append(
            {
                "id": e.id,
                "title": e.title,
                "year": e.year,
                "semester": e.semester,
                "edict_type": e.edict_type,
                "is_open": e.is_open,
            }
        )
    return out


@router.post("")
async def create_edict(
    payload: InsertEdictSchema,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    _check_dates(payload)
    now = dt.datetime.now(dt.timezone.utc)
    edict = Edict(
        title=payload.title,
        description=payload.description,
        candidate_forms=str(payload.candidate_forms),
        recommenders_forms=str(payload.recommenders_forms),
        closed_date=payload.date_closed.date(),
        year=payload.year,
        semester=payload.semester,
        edict_type=payload.edict_type,
        phase="inscricoes",
        is_open=payload.is_open,
        created_at=now,
        updated_at=now,
        user_id=user.id,
    )
    db.add(edict)
    await db.flush()
    for label, closed in _phase_dates(payload).items():
        db.add(EdictPhase(edict_id=edict.id, phase=label, closed_date=closed))
    await db.commit()
    return {
        "title": edict.title,
        "description": edict.description,
        "year": edict.year,
        "semester": edict.semester,
        "edict_type": edict.edict_type,
        "is_open": edict.is_open,
        "candidate_forms": payload.candidate_forms,
        "recommenders_forms": payload.recommenders_forms,
        "date_application": payload.date_application,
        "date_verification": payload.date_verification,
        "date_evaluation": payload.date_evaluation,
        "date_closed": payload.date_closed,
        "id": edict.id,
        "closed_date": payload.date_closed,
    }


@router.get("/{edict_id}")
async def get_edict(
    edict_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    phases = (
        await db.execute(
            select(EdictPhase)
            .where(EdictPhase.edict_id == edict.id)
            .order_by(EdictPhase.id)
        )
    ).scalars().all()
    slot = (
        await db.execute(
            select(UserEdictSlot).where(
                UserEdictSlot.user_id == user.id,
                UserEdictSlot.edict_id == edict.id,
            )
        )
    ).scalar_one_or_none()
    slots = str(slot.slots) if slot is not None and slot.slots is not None else "0"
    return {
        "id": edict.id,
        "title": edict.title,
        "candidate_form_id": str(edict.candidate_forms or ""),
        "recommender_form_id": str(edict.recommenders_forms or ""),
        "description": edict.description or "",
        "closed_date": edict.closed_date,
        "created_at": edict.created_at,
        "year": edict.year,
        "semester": edict.semester,
        "type": edict.edict_type,
        "is_open": edict.is_open,
        "updated_at": edict.updated_at,
        "phase": edict.phase,
        "phases": [
            {"id": p.id, "closed_date": p.closed_date, "phase": p.phase}
            for p in phases
        ],
        "slots": slots,
    }


@router.post("/{edict_id}/edit")
async def edit_edict(
    edict_id: int,
    payload: EditEdictSchema,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    _check_dates(payload)
    edict.title = payload.title
    edict.description = payload.description
    edict.year = int(payload.year)
    edict.semester = int(payload.semester)
    edict.edict_type = payload.edict_type
    edict.closed_date = payload.date_closed.date()
    edict.updated_at = dt.datetime.now(dt.timezone.utc)
    phases = (
        await db.execute(select(EdictPhase).where(EdictPhase.edict_id == edict.id))
    ).scalars().all()
    by_label = {p.phase: p for p in phases}
    for label, closed in _phase_dates(payload).items():
        if label in by_label:
            by_label[label].closed_date = closed
    await db.commit()
    return {
        "title": payload.title,
        "description": payload.description,
        "year": payload.year,
        "semester": payload.semester,
        "edict_type": payload.edict_type,
        "date_application": payload.date_application,
        "date_verification": payload.date_verification,
        "date_evaluation": payload.date_evaluation,
        "date_closed": payload.date_closed,
    }


@router.post("/{edict_id}/edit-date")
async def edit_edict_date(
    edict_id: int,
    payload: EditEdictDateSchema,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    edict.closed_date = payload.closed_date
    phases = (
        await db.execute(select(EdictPhase).where(EdictPhase.edict_id == edict.id))
    ).scalars().all()
    for phase in phases:
        if phase.phase == "encerrado":
            phase.closed_date = payload.closed_date
    await db.commit()
    return {"closed_date": payload.closed_date}


@router.post("/{edict_id}/advance-phase")
async def advance_phase(
    edict_id: int,
    payload: AdvancePhaseEdictSchema,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    edict = await _get_edict(db, edict_id)
    phase = (
        await db.execute(
            select(EdictPhase).where(
                EdictPhase.id == payload.id, EdictPhase.edict_id == edict.id
            )
        )
    ).scalar_one_or_none()
    if phase is None:
        phase = await db.get(EdictPhase, payload.id)
    if phase is None:
        raise HTTPException(status_code=404, detail="Fase não encontrada")
    edict.phase = phase.phase
    edict.updated_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()

    forms_phase = forms_db.FORM_PHASE_BY_EDICT_PHASE.get(phase.phase)
    if forms_phase and edict.candidate_forms:
        try:
            await forms_db.change_form_phase(fdb, int(edict.candidate_forms), forms_phase)
        except (TypeError, ValueError):
            pass
    return {"id": phase.id, "label": phase.phase}


@router.delete("/{edict_id}/remove")
async def remove_edict(
    edict_id: int,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    await db.delete(edict)
    await db.commit()
    return {"message": "Edital removido com sucesso"}


@router.patch("/{edict_id}/close")
async def close_edict(
    edict_id: int,
    payload: CloseEdictSchema,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    if not edict.is_open:
        raise HTTPException(status_code=409, detail="Edital já encerrado")
    edict.is_open = False
    edict.updated_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()
    return {"message": "Edital encerrado"}


@router.post("/{edict_id}/slots")
async def set_user_slots(
    edict_id: int,
    payload: SlotsSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_edict(db, edict_id)
    amount = (payload.amount or "").strip()
    if amount == "":
        amount = 0
    else:
        try:
            amount = int(amount)
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
    ).scalar_one_or_none()
    if slot is None:
        db.add(UserEdictSlot(user_id=user.id, edict_id=edict_id, slots=amount))
    else:
        slot.slots = amount
    await db.commit()
    return {"amount": str(amount)}


# ---------------------------------------------------------------------------
# Mapeamentos de formulários
# ---------------------------------------------------------------------------


FORM_TYPE_BY_TIPO = {"candidates": "candidate", "recommenders": "recommender"}


async def _validate_tree(fdb: AsyncSession, form_id: int, version: int, tree: dict):
    fields = await forms_db.get_all_fields(fdb, form_id)
    version_fields = [f for f in fields if (f["version"] or 1) == version]
    if not version_fields:
        version_fields = fields
    valid_pairs = {(f["section_id"], f["id"]) for f in version_fields}
    # Fallback: ids existentes em qualquer formulário do Forms.
    all_field_ids = {
        row["id"] for row in (await fdb.execute(text("select id from form_field"))).mappings()
    }
    all_section_ids = {
        row["id"] for row in (await fdb.execute(text("select id from form_section"))).mappings()
    }
    for leaf in mappings_svc.flatten(tree).values():
        try:
            section = int(leaf["section"])
            field = int(leaf["field"])
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="Referência seção/campo inválida")
        if (section, field) in valid_pairs:
            continue
        if field in all_field_ids and section in all_section_ids:
            continue
        raise HTTPException(status_code=422, detail="Referência seção/campo inválida")


async def _create_mapping(
    edict_id: int,
    form_type: str,
    version: int,
    tree: dict,
    user,
    db: AsyncSession,
    fdb: AsyncSession,
):
    edict = await _get_edict(db, edict_id)
    form_id = (
        edict.candidate_forms if form_type == "candidate" else edict.recommenders_forms
    )
    if not form_id:
        raise HTTPException(status_code=404, detail="Formulário não configurado")
    await _validate_tree(fdb, int(form_id), version, tree)

    existing = (
        await db.execute(
            select(EdictFormMapping).where(
                EdictFormMapping.edict_id == edict.id,
                EdictFormMapping.form_type == form_type,
                EdictFormMapping.form_version == version,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Mapeamento já existe")

    mapping = EdictFormMapping(
        edict_id=edict.id,
        form_type=form_type,
        mapping=tree,
        is_active=True,
        created_at=dt.datetime.now(dt.timezone.utc),
        form_id=str(form_id),
        user_id=user.id,
        form_version=version,
    )
    db.add(mapping)
    await db.commit()
    return {
        "id": mapping.id,
        "edict_id": mapping.edict_id,
        "form_type": mapping.form_type,
        "user_id": mapping.user_id,
        "form_version": mapping.form_version,
        "mapping": mapping.mapping,
        "is_active": mapping.is_active,
    }


async def _list_mappings(edict_id: int, form_type: str, db: AsyncSession):
    await _get_edict(db, edict_id)
    rows = (
        await db.execute(
            select(EdictFormMapping)
            .where(
                EdictFormMapping.edict_id == edict_id,
                EdictFormMapping.form_type == form_type,
                EdictFormMapping.is_active.is_(True),
            )
            .order_by(EdictFormMapping.form_version)
        )
    ).scalars().all()
    return mappings_svc.merge_trees([r.mapping for r in rows])


async def _find_mapping(db: AsyncSession, edict_id, form_type, version, mapping_id):
    mapping = (
        await db.execute(
            select(EdictFormMapping).where(
                EdictFormMapping.edict_id == edict_id,
                EdictFormMapping.form_type == form_type,
                EdictFormMapping.form_version == version,
                EdictFormMapping.id == mapping_id,
            )
        )
    ).scalar_one_or_none()
    if mapping is None:
        mapping = await db.get(EdictFormMapping, mapping_id)
    if mapping is None:
        raise HTTPException(status_code=404, detail="Mapeamento não encontrado")
    return mapping


async def _update_mapping(
    edict_id: int,
    form_type: str,
    version: int,
    mapping_id: int,
    payload: dict,
    db: AsyncSession,
):
    await _get_edict(db, edict_id)
    mapping = await _find_mapping(db, edict_id, form_type, version, mapping_id)
    mapping.mapping = payload
    await db.commit()
    return {
        "id": mapping.id,
        "edict_id": mapping.edict_id,
        "form_type": mapping.form_type,
        "form_version": mapping.form_version,
        "mapping": mapping.mapping,
        "is_active": mapping.is_active,
    }


async def _delete_mapping(
    edict_id: int,
    form_type: str,
    version: int,
    mapping_id: int,
    db: AsyncSession,
):
    await _get_edict(db, edict_id)
    mapping = await _find_mapping(db, edict_id, form_type, version, mapping_id)
    await db.delete(mapping)
    await db.commit()
    return {"message": "Mapping deleted successfully"}


async def _unmapped_versions(edict_id: int, form_type: str, db: AsyncSession):
    await _get_edict(db, edict_id)
    subs = (
        await db.execute(select(Submission).where(Submission.edict_id == edict_id))
    ).scalars().all()
    if form_type == "candidate":
        versions = {s.candidate_form_version for s in subs}
    else:
        versions = {s.recommender_form_version for s in subs}
    mapped = {
        m.form_version
        for m in (
            await db.execute(
                select(EdictFormMapping).where(
                    EdictFormMapping.edict_id == edict_id,
                    EdictFormMapping.form_type == form_type,
                )
            )
        ).scalars()
    }
    return sorted(v for v in versions if v not in mapped)


def _register_mapping_routes(tipo: str):
    """Rotas literais por tipo (candidates/recommenders), como no contrato
    OpenAPI original."""
    form_type = FORM_TYPE_BY_TIPO[tipo]

    @router.post(f"/{{edict_id}}/{tipo}/mappings/versions/{{version}}/")
    @router.post(f"/{{edict_id}}/{tipo}/mappings/versions/{{version}}")
    async def create_mapping(
        edict_id: int,
        version: int,
        tree: dict = Body(...),
        user=Depends(require_admin),
        db: AsyncSession = Depends(get_db),
        fdb: AsyncSession = Depends(get_forms_db),
    ):
        return await _create_mapping(edict_id, form_type, version, tree, user, db, fdb)

    @router.get(f"/{{edict_id}}/{tipo}/mappings")
    async def get_mappings(
        edict_id: int,
        user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await _list_mappings(edict_id, form_type, db)

    @router.put(f"/{{edict_id}}/{tipo}/mappings/versions/{{version}}/{{mapping_id}}")
    async def update_mapping(
        edict_id: int,
        version: int,
        mapping_id: int,
        payload: dict = Body(...),
        user=Depends(require_admin),
        db: AsyncSession = Depends(get_db),
    ):
        return await _update_mapping(edict_id, form_type, version, mapping_id, payload, db)

    @router.delete(f"/{{edict_id}}/{tipo}/mappings/versions/{{version}}/{{mapping_id}}")
    async def delete_mapping(
        edict_id: int,
        version: int,
        mapping_id: int,
        user=Depends(require_admin),
        db: AsyncSession = Depends(get_db),
    ):
        return await _delete_mapping(edict_id, form_type, version, mapping_id, db)

    @router.get(f"/{{edict_id}}/{tipo}/forms/versions/unmapped")
    async def get_unmapped_versions(
        edict_id: int,
        user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await _unmapped_versions(edict_id, form_type, db)


_register_mapping_routes("candidates")
_register_mapping_routes("recommenders")


# ---------------------------------------------------------------------------
# Inscrições do edital
# ---------------------------------------------------------------------------


@router.get("/{edict_id}/submissions")
async def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    edict = await _get_edict(db, edict_id)
    await submissions_data.sync_submissions(db, fdb, edict)
    subs = (
        await db.execute(
            select(Submission).where(Submission.edict_id == edict.id).order_by(Submission.id)
        )
    ).scalars().all()
    if only_favorites:
        favs = {
            f.submission_id
            for f in (
                await db.execute(
                    select(Favorite).where(Favorite.user_id == user.id)
                )
            ).scalars()
        }
        subs = [s for s in subs if s.id in favs]
    if stats is not None:
        subs = [s for s in subs if s.stats == stats]
    cand_mappings = await submissions_data.load_mappings(db, edict.id, "candidate")
    items = []
    for sub in subs:
        items.append(
            await submissions_data.build_item(db, fdb, sub, edict, user, cand_mappings)
        )
    return {"submissions": items}


# ---------------------------------------------------------------------------
# Relatórios
# ---------------------------------------------------------------------------


@router.post("/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: int,
    mode: str = "plain_text",
    sections: SectionsDocument = Body(default=SectionsDocument()),
    background: BackgroundTasks = None,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    edict = await _get_edict(db, edict_id)
    subs = (
        await db.execute(select(Submission).where(Submission.edict_id == edict.id))
    ).scalars().all()
    sub_ids = [s.id for s in subs]

    user_ids: set[int] = set()
    if sub_ids:
        for model in (Comment, Favorite, Label, PrivateNote):
            rows = (
                await db.execute(
                    select(model.user_id).where(model.submission_id.in_(sub_ids))
                )
            ).scalars().all()
            user_ids.update(rows)

    interactors = []
    for uid in sorted(user_ids):
        u = await db.get(User, uid)
        if u:
            interactors.append({"id": u.id, "name": u.name, "email": u.email})

    if mode != "pdf":
        return interactors

    data = {
        "statistics_lines": [],
        "approved_lines": [],
        "refused_lines": [],
        "underreview_lines": [],
        "advisor_lines": [],
        "email_lines": [],
    }
    if sections.general_statistics:
        try:
            responses = await forms_db.get_submitted_responses(
                fdb, int(edict.candidate_forms)
            )
        except (TypeError, ValueError):
            responses = []
        finished = len(responses)
        in_progress = 0
        try:
            all_fields = await forms_db.get_all_fields(fdb, int(edict.candidate_forms))
        except (TypeError, ValueError):
            all_fields = []
        data["statistics_lines"] = [
            f"Candidaturas finalizadas: {finished}",
            f"Candidaturas em preenchimento: {in_progress}",
            f"Total de inscricoes registradas: {len(subs)}",
        ]
    for sub in subs:
        line = f"#{sub.id} - {sub.stats}"
        if sections.approved and sub.stats == "approved":
            data["approved_lines"].append(line)
        if sections.refused and sub.stats == "refused":
            data["refused_lines"].append(line)
        if sections.underreview and sub.stats == "underreview":
            data["underreview_lines"].append(line)
    if sections.list_of_advisors or sections.relation:
        for sub in subs:
            if sub.advisor_id:
                adv = await db.get(User, sub.advisor_id)
                if adv:
                    data["advisor_lines"].append(f"{adv.name} <{adv.email}>")
    if sections.show_emails:
        data["email_lines"] = [i["email"] for i in interactors if i["email"]]

    job_id = reports.new_job_id()
    background.add_task(reports.generate_pdf, job_id, edict, data)
    return {"job_id": job_id, "status": "processing"}


@router.post("/{edict_id}/pairing-biddings")
async def pairing_biddings(
    edict_id: int,
    background: BackgroundTasks = None,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    edict = await _get_edict(db, edict_id)
    subs = (
        await db.execute(
            select(Submission).where(Submission.edict_id == edict.id).order_by(Submission.id)
        )
    ).scalars().all()
    sub_ids = [s.id for s in subs]
    if not sub_ids:
        biddings = []
    else:
        biddings = (
            await db.execute(
                select(Label).where(
                    Label.context_type == "bidding",
                    Label.submission_id.in_(sub_ids),
                )
            )
        ).scalars().all()
    by_sub: dict[int, list[Label]] = {}
    for b in biddings:
        by_sub.setdefault(b.submission_id, []).append(b)

    teachers: dict[int, User] = {}
    for labels in by_sub.values():
        for b in labels:
            if b.user_id not in teachers:
                u = await db.get(User, b.user_id)
                if u:
                    teachers[b.user_id] = u
    ordered = [teachers[uid] for uid in sorted(teachers)]

    slots_by_user = {}
    for t in ordered:
        slot = (
            await db.execute(
                select(UserEdictSlot).where(
                    UserEdictSlot.user_id == t.id,
                    UserEdictSlot.edict_id == edict.id,
                )
            )
        ).scalar_one_or_none()
        slots_by_user[t.id] = str(slot.slots) if slot and slot.slots is not None else "0"

    cand_mappings = await submissions_data.load_mappings(db, edict.id, "candidate")
    rows = [["#"] + [t.email or "" for t in ordered]]
    rows.append(["slots"] + [slots_by_user[t.id] for t in ordered])
    for sub in subs:
        leaves = submissions_data._leaves_for_version(
            cand_mappings, sub.candidate_form_version
        )
        values = await forms_db.get_values(fdb, sub.candidate_form_id)
        email = mappings_svc.get_value(leaves, values, "email") or ""
        row = ["" for _ in ordered]
        for b in by_sub.get(sub.id, []):
            if b.user_id in teachers:
                row[ordered.index(teachers[b.user_id])] = b.label
        rows.append([email] + row)

    job_id = reports.new_job_id()
    if background is not None:
        background.add_task(reports.generate_csv, job_id, rows)
    return {"job_id": job_id, "status": "processing"}


def _job_path(job_id: str, ext: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9\-]+", job_id):
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return os.path.join(reports.JOBS_DIR, f"{job_id}.{ext}")


@router.get("/download_pdf/{job_id}")
async def download_pdf(job_id: str, background: BackgroundTasks = None):
    path = _job_path(job_id, "pdf")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    if background is not None:
        background.add_task(os.remove, path)
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"{job_id}.pdf",
        content_disposition_type="inline",
    )


@router.get("/download_csv/{job_id}")
async def download_csv(job_id: str, background: BackgroundTasks = None):
    path = _job_path(job_id, "csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    if background is not None:
        background.add_task(os.remove, path)
    return FileResponse(
        path,
        media_type="text/csv",
        filename=f"{job_id}.csv",
        content_disposition_type="inline",
    )
