"""Rotas de editais, mapeamentos e relatórios."""
import json
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text

from auth.session import CurrentUser, get_current_user, require_admin
from database import get_db, get_forms_db
from schemas import (
    AdvancePhaseEdictSchema,
    CloseEdictSchema,
    EditEdictDateSchema,
    EditEdictSchema,
    InsertEdictSchema,
    SectionsDocument,
    SlotsSchema,
)
from services import forms_service, mail, reports, submissions as subs_service

router = APIRouter(prefix="/edicts", tags=["edicts"])

PHASE_DATES = [
    ("inscricoes", "date_application"),
    ("avaliacao", "date_verification"),
    ("homologacao", "date_evaluation"),
    ("encerrado", "date_closed"),
]
FORMS_PHASE = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}


async def _get_edict(db, edict_id: int) -> dict:
    row = (
        await db.execute(text("SELECT * FROM edict WHERE id = :i"), {"i": edict_id})
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    return dict(row)


def _validate_dates(payload) -> None:
    dates = [payload.date_application, payload.date_verification, payload.date_evaluation, payload.date_closed]
    if any(dates[i] > dates[i + 1] for i in range(len(dates) - 1)):
        raise HTTPException(status_code=400, detail="Datas fora de ordem")


@router.get("")
async def get_all_edicts(
    type: str | None = None,
    is_open: bool | None = None,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    clauses, params = ["1=1"], {}
    if type is not None:
        clauses.append("type = :t")
        params["t"] = type
    if is_open is not None:
        clauses.append("is_open = :o")
        params["o"] = is_open
    rows = (
        await db.execute(
            text(
                "SELECT id, title, year, semester, type, is_open FROM edict "
                f"WHERE {' AND '.join(clauses)} ORDER BY closed_date DESC, id DESC"
            ),
            params,
        )
    ).mappings().all()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "year": r["year"],
            "semester": r["semester"],
            "edict_type": r["type"],
            "is_open": r["is_open"],
        }
        for r in rows
    ]


@router.post("")
async def create_edict(
    payload: InsertEdictSchema,
    user: CurrentUser = Depends(require_admin),
    db=Depends(get_db),
):
    _validate_dates(payload)
    edict_id = (
        await db.execute(
            text(
                "INSERT INTO edict(title, description, candidate_forms, recommenders_forms, "
                "closed_date, year, semester, type, phase, is_open, created_at, updated_at, user_id) "
                "VALUES (:ti, :de, :cf, :rf, :cd, :y, :se, :ty, 'inscricoes', :io, now(), now(), :u) "
                "RETURNING id"
            ),
            {
                "ti": payload.title,
                "de": payload.description,
                "cf": str(payload.candidate_forms),
                "rf": str(payload.recommenders_forms),
                "cd": payload.date_closed,
                "y": payload.year,
                "se": payload.semester,
                "ty": payload.edict_type,
                "io": payload.is_open,
                "u": user.id,
            },
        )
    ).scalar()
    for phase, attr in PHASE_DATES:
        await db.execute(
            text("INSERT INTO edict_phase(edict_id, closed_date, phase) VALUES (:e, :d, :p)"),
            {"e": edict_id, "d": getattr(payload, attr), "p": phase},
        )
    await db.commit()
    return {
        "id": edict_id,
        "title": payload.title,
        "description": payload.description,
        "year": payload.year,
        "semester": payload.semester,
        "edict_type": payload.edict_type,
        "is_open": payload.is_open,
        "candidate_forms": payload.candidate_forms,
        "recommenders_forms": payload.recommenders_forms,
        "date_application": payload.date_application,
        "date_verification": payload.date_verification,
        "date_evaluation": payload.date_evaluation,
        "date_closed": payload.date_closed,
        "closed_date": payload.date_closed,
    }


@router.get("/download_pdf/{job_id}")
async def download_pdf(job_id: str):
    return _download(job_id, "application/pdf")


@router.get("/download_csv/{job_id}")
async def download_csv(job_id: str):
    return _download(job_id, "text/csv; charset=utf-8")


def _download(job_id: str, media_type: str):
    path = reports.JOBS.get(job_id)
    if not path or not Path(path).is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    del reports.JOBS[job_id]
    return FileResponse(path, media_type=media_type, headers={"content-disposition": "inline"})


@router.get("/{edict_id}")
async def get_edict(
    edict_id: int, user=Depends(get_current_user), db=Depends(get_db)
):
    edict = await _get_edict(db, edict_id)
    phases = (
        await db.execute(
            text(
                "SELECT id, phase, closed_date FROM edict_phase WHERE edict_id = :e ORDER BY id"
            ),
            {"e": edict_id},
        )
    ).mappings().all()
    slots = (
        await db.execute(
            text("SELECT slots FROM user_edict_slots WHERE user_id = :u AND edict_id = :e"),
            {"u": user.id, "e": edict_id},
        )
    ).scalar()
    return {
        "id": edict["id"],
        "title": edict["title"],
        "candidate_form_id": edict["candidate_forms"],
        "recommender_form_id": edict["recommenders_forms"],
        "description": edict["description"],
        "closed_date": edict["closed_date"],
        "created_at": edict["created_at"],
        "year": edict["year"],
        "semester": edict["semester"],
        "type": edict["type"],
        "is_open": edict["is_open"],
        "updated_at": edict["updated_at"],
        "phase": edict["phase"],
        "phases": [dict(p) for p in phases],
        "slots": str(slots) if slots is not None else "0",
    }


@router.get("/{edict_id}/submissions")
async def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    edict = await _get_edict(db, edict_id)
    synced = await subs_service.sync_edict_submissions(db, fdb, edict)
    items = []
    for entry in synced:
        if stats is not None and entry["submission"]["stats"] != stats:
            continue
        item = await subs_service.build_listing_item(db, fdb, edict, entry, user.id)
        if only_favorites and not item["is_favorite"]:
            continue
        items.append(item)
    return {"submissions": items}


@router.post("/{edict_id}/edit")
async def edit_date_edict(
    edict_id: int,
    payload: EditEdictSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    await _get_edict(db, edict_id)
    _validate_dates(payload)
    await db.execute(
        text(
            "UPDATE edict SET title = :ti, description = :de, year = :y, semester = :se, "
            "type = :ty, closed_date = :cd, updated_at = now() WHERE id = :i"
        ),
        {
            "ti": payload.title,
            "de": payload.description,
            "y": int(payload.year),
            "se": int(payload.semester),
            "ty": payload.edict_type,
            "cd": payload.date_closed,
            "i": edict_id,
        },
    )
    for phase, attr in PHASE_DATES:
        await db.execute(
            text("UPDATE edict_phase SET closed_date = :d WHERE edict_id = :e AND phase = :p"),
            {"d": getattr(payload, attr), "e": edict_id, "p": phase},
        )
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
async def edit_edict_date_only(
    edict_id: int,
    payload: EditEdictDateSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    await _get_edict(db, edict_id)
    await db.execute(
        text("UPDATE edict SET closed_date = :d, updated_at = now() WHERE id = :i"),
        {"d": payload.closed_date, "i": edict_id},
    )
    await db.execute(
        text("UPDATE edict_phase SET closed_date = :d WHERE edict_id = :e AND phase = 'encerrado'"),
        {"d": payload.closed_date, "e": edict_id},
    )
    await db.commit()
    return {"closed_date": payload.closed_date}


@router.post("/{edict_id}/advance-phase")
async def advance_edict(
    edict_id: int,
    payload: AdvancePhaseEdictSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    await _get_edict(db, edict_id)
    phase_row = (
        await db.execute(
            text("SELECT id, phase FROM edict_phase WHERE id = :i AND edict_id = :e"),
            {"i": payload.id, "e": edict_id},
        )
    ).first()
    if not phase_row:
        raise HTTPException(status_code=404, detail="Fase não encontrada")
    await db.execute(
        text("UPDATE edict SET phase = :p, updated_at = now() WHERE id = :i"),
        {"p": phase_row.phase, "i": edict_id},
    )
    await db.commit()
    forms_phase = FORMS_PHASE.get(phase_row.phase)
    if forms_phase:
        edict = await _get_edict(db, edict_id)
        for column in ("candidate_forms", "recommenders_forms", "accept_forms"):
            form_id = subs_service.to_int(edict.get(column))
            if form_id:
                await fdb.execute(
                    text("SELECT id, phase FROM change_form_phase(:f, CAST(:p AS form_phase))"),
                    {"f": form_id, "p": forms_phase},
                )
        await fdb.commit()
    return {"id": phase_row.id, "label": phase_row.phase}


@router.delete("/{edict_id}/remove")
async def remove_edict(edict_id: int, user=Depends(require_admin), db=Depends(get_db)):
    await _get_edict(db, edict_id)
    await db.execute(text("DELETE FROM edict WHERE id = :i"), {"i": edict_id})
    await db.commit()
    return {"message": "Edital removido com sucesso"}


@router.post("/{edict_id}/slots")
async def set_user_slots(
    edict_id: int,
    payload: SlotsSchema,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    await _get_edict(db, edict_id)
    try:
        amount = int(payload.amount)
    except (TypeError, ValueError):
        amount = 0
    if amount < 0:
        amount = 0
    await db.execute(
        text(
            "INSERT INTO user_edict_slots(user_id, edict_id, slots) VALUES (:u, :e, :s) "
            "ON CONFLICT (user_id, edict_id) DO UPDATE SET slots = :s"
        ),
        {"u": user.id, "e": edict_id, "s": amount},
    )
    await db.commit()
    return {"amount": str(amount)}


@router.patch("/{edict_id}/close")
async def close_edict(
    edict_id: int,
    payload: CloseEdictSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    edict = await _get_edict(db, edict_id)
    if not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edital já encerrado")
    await db.execute(
        text("UPDATE edict SET is_open = false, updated_at = now() WHERE id = :i"),
        {"i": edict_id},
    )
    await db.commit()
    if payload.send_approval_letter:
        synced = await subs_service.sync_edict_submissions(db, fdb, edict)
        for entry in synced:
            if entry["submission"]["stats"] != "approved":
                continue
            data = entry["data"]
            if data["email"]:
                mail.send_letter_email(data["name"] or "", data["email"])
    return {"message": "Edital encerrado"}


@router.post("/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: int,
    background_tasks: BackgroundTasks,
    mode: str = "plain_text",
    payload: SectionsDocument | None = Body(default=None),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    await _get_edict(db, edict_id)
    if mode == "pdf":
        job_id, path = reports.create_job("pdf")
        background_tasks.add_task(reports.generate_pdf_report, edict_id, payload or SectionsDocument(), path)
        return {"status": "processing", "job_id": job_id}
    return await reports.get_interactors(db, edict_id)


@router.post("/{edict_id}/pairing-biddings")
async def pairing_biddings(
    edict_id: int,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    await _get_edict(db, edict_id)
    job_id, path = reports.create_job("csv")
    background_tasks.add_task(reports.generate_pairing_csv, edict_id, path)
    return {"status": "processing", "job_id": job_id}


def _mapping_form_column(kind: str) -> str:
    return "candidate_forms" if kind == "candidate" else "recommenders_forms"


def _collect_leaves(tree, out: list):
    for value in tree.values():
        if value is None:
            continue
        if subs_service.is_leaf(value):
            out.append((value["section"], value["field"]))
        elif isinstance(value, dict):
            _collect_leaves(value, out)


async def _create_mapping(db, fdb, edict_id: int, kind: str, version: int, tree: dict, user: CurrentUser):
    edict = await _get_edict(db, edict_id)
    form_id = subs_service.to_int(edict.get(_mapping_form_column(kind)))
    if not form_id:
        raise HTTPException(status_code=404, detail="Edital sem formulário deste tipo")
    leaves: list[tuple[int, int]] = []
    _collect_leaves(tree, leaves)
    valid = await forms_service.valid_leaf_pairs(fdb, form_id, version)
    for leaf in leaves:
        if leaf not in valid:
            raise HTTPException(status_code=422, detail=f"Referência inválida: seção {leaf[0]}, campo {leaf[1]}")
    row = (
        await db.execute(
            text(
                "INSERT INTO edict_form_mappings(edict_id, form_type, mapping, is_active, "
                "form_id, user_id, form_version) "
                "VALUES (:e, :t, :m, true, :f, :u, :v) "
                "RETURNING id, edict_id, form_type, mapping, is_active, created_at, form_id, "
                "user_id, form_version"
            ),
            {
                "e": edict_id,
                "t": kind,
                "m": json.dumps(tree),
                "f": str(form_id),
                "u": user.id,
                "v": version,
            },
        )
    ).mappings().first()
    await db.commit()
    result = dict(row)
    result["version"] = result["form_version"]
    return result


@router.post("/{edict_id}/recommenders/mappings/versions/{version}/")
async def create_recommender_form_mapping(
    edict_id: int,
    version: int,
    tree: dict = Body(...),
    user: CurrentUser = Depends(require_admin),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    return await _create_mapping(db, fdb, edict_id, "recommender", version, tree, user)


@router.post("/{edict_id}/candidates/mappings/versions/{version}/")
async def create_candidate_form_mapping(
    edict_id: int,
    version: int,
    tree: dict = Body(...),
    user: CurrentUser = Depends(require_admin),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    return await _create_mapping(db, fdb, edict_id, "candidate", version, tree, user)


@router.get("/{edict_id}/candidates/mappings")
async def get_submission_form_mapping(
    edict_id: int, user=Depends(get_current_user), db=Depends(get_db)
):
    await _get_edict(db, edict_id)
    return await forms_service.fetch_mappings(db, edict_id, "candidate")


@router.get("/{edict_id}/recommenders/mappings")
async def get_recommender_form_mapping(
    edict_id: int, user=Depends(get_current_user), db=Depends(get_db)
):
    await _get_edict(db, edict_id)
    return await forms_service.fetch_mappings(db, edict_id, "recommender")


async def _find_mapping(db, edict_id: int, kind: str, version: int, mapping_id: int) -> dict:
    row = (
        await db.execute(
            text(
                "SELECT id, edict_id, form_type, mapping, is_active, created_at, form_id, "
                "user_id, form_version FROM edict_form_mappings "
                "WHERE id = :i AND edict_id = :e AND form_type = :t AND form_version = :v"
            ),
            {"i": mapping_id, "e": edict_id, "t": kind, "v": version},
        )
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Mapeamento não encontrado")
    return dict(row)


@router.put("/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
async def update_recommender_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    payload: dict = Body(...),
    user=Depends(require_admin),
    db=Depends(get_db),
):
    await _find_mapping(db, edict_id, "recommender", version, mapping_id)
    await db.execute(
        text("UPDATE edict_form_mappings SET mapping = :m WHERE id = :i"),
        {"m": json.dumps(payload), "i": mapping_id},
    )
    await db.commit()
    return await _find_mapping(db, edict_id, "recommender", version, mapping_id)


@router.put("/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
async def update_candidate_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    payload: dict = Body(...),
    user=Depends(require_admin),
    db=Depends(get_db),
):
    await _find_mapping(db, edict_id, "candidate", version, mapping_id)
    await db.execute(
        text("UPDATE edict_form_mappings SET mapping = :m WHERE id = :i"),
        {"m": json.dumps(payload), "i": mapping_id},
    )
    await db.commit()
    return await _find_mapping(db, edict_id, "candidate", version, mapping_id)


@router.delete("/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
async def delete_recommender_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    await _find_mapping(db, edict_id, "recommender", version, mapping_id)
    await db.execute(text("DELETE FROM edict_form_mappings WHERE id = :i"), {"i": mapping_id})
    await db.commit()
    return {"message": "Mapping deleted successfully"}


@router.delete("/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
async def delete_candidate_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    await _find_mapping(db, edict_id, "candidate", version, mapping_id)
    await db.execute(text("DELETE FROM edict_form_mappings WHERE id = :i"), {"i": mapping_id})
    await db.commit()
    return {"message": "Mapping deleted successfully"}


@router.get("/{edict_id}/candidates/forms/versions/unmapped")
async def get_candidates_unmapped_versions(
    edict_id: int, user=Depends(get_current_user), db=Depends(get_db), fdb=Depends(get_forms_db)
):
    return await _unmapped_versions(db, fdb, edict_id, "candidate")


@router.get("/{edict_id}/recommenders/forms/versions/unmapped")
async def get_recommenders_unmapped_versions(
    edict_id: int, user=Depends(get_current_user), db=Depends(get_db), fdb=Depends(get_forms_db)
):
    return await _unmapped_versions(db, fdb, edict_id, "recommender")


async def _unmapped_versions(db, fdb, edict_id: int, kind: str) -> list[int]:
    edict = await _get_edict(db, edict_id)
    form_id = subs_service.to_int(edict.get(_mapping_form_column(kind)))
    if not form_id:
        return []
    versions = await forms_service.form_versions(fdb, form_id)
    mapped = {m["form_version"] for m in await forms_service.fetch_mappings(db, edict_id, kind)}
    return [v for v in versions if v not in mapped]
