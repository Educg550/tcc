"""Inscrições, consulta, avaliação, orientação e comunicação."""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import FileResponse

from auth import ADMIN_ROLES, current_user
from config import settings
from db import get_db, get_forms_db
from models import (Bidding, Comment, Edict, Favorite, Label, Mapping,
                    Phase, PrivateNote, Submission, User, View)
import forms_db
from mailing import send_mail

router = APIRouter()

TZ = ZoneInfo("America/Sao_Paulo")
BIDDING_VALUES = {"decline", "available", "interested", "agreed", "interested_scholarship", ""}
STATS_VALUES = {"approved", "refused", "underreview", "waitlist"}
SEMESTER_MAP = {
    "first": "Primeiro semestre.", "primeiro": "Primeiro semestre.",
    "1": "Primeiro semestre.",
    "second": "Segundo semestre.", "segundo": "Segundo semestre.",
    "2": "Segundo semestre.",
}


def _get_sub(db, submission_id):
    sub = db.get(Submission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return sub


def _phase_label(db, sub):
    edict = db.get(Edict, sub.edict_id)
    if not edict or not edict.current_phase_id:
        return None
    phase = db.get(Phase, edict.current_phase_id)
    return phase.label if phase else None


def _require_phase(db, sub, label):
    if _phase_label(db, sub) != label:
        raise HTTPException(status_code=400, detail=f"Phase must be {label}")


def _eval_tree(tree, values):
    """Avalia a árvore de mapeamento contra os valores da resposta."""
    if tree is None:
        return None
    if isinstance(tree, dict) and set(tree) == {"section", "field"}:
        return values.get((str(tree["section"]), str(tree["field"])))
    if isinstance(tree, dict):
        return {k: _eval_tree(v, values) for k, v in tree.items()}
    return tree


def _answer_values_map(fs, answer_id):
    vals = {}
    for row in forms_db.answer_values(fs, answer_id):
        vals[(str(row["section_id"]), str(row["field_id"]))] = row["value"]
        # indexação alternativa por nome, para associação de recomendações
        vals[(str(row["section_id"]), str(row["name"]))] = row["value"]
        vals[("name:" + str(row["name"]), "")] = row["value"]
    return vals


def _flat_values(fs, answer_id):
    """Lista de valores com metadados completos dos campos."""
    return forms_db.answer_values(fs, answer_id)


def _candidate_email(fs, answer_id):
    for row in forms_db.answer_values(fs, answer_id):
        name = (row.get("name") or "").lower()
        label = (row.get("label") or "").lower()
        if "email" in name or "email" in label or "e-mail" in label:
            v = row.get("value")
            if v and "@" in str(v):
                return str(v)
    ans = forms_db.get_answer(fs, answer_id)
    return ans.get("email") if ans else None


def _recommendations(db, fs, edict, sub):
    """Recomendações do Forms associadas à inscrição pelos dados do candidato."""
    if not edict.recommender_form_id:
        return []
    cand_email = _candidate_email(fs, sub.answer_id)
    recs = []
    for ans in forms_db.answers_for_form(fs, edict.recommender_form_id):
        if not ans.get("finalized"):
            continue
        values = forms_db.answer_values(fs, ans["id"])
        text = " ".join(str(v.get("value") or "").lower() for v in values)
        if cand_email and cand_email.lower() not in text:
            continue
        rec_email = ans.get("email") or _candidate_email(fs, ans["id"])
        rec_name = ""
        for v in values:
            if (v.get("name") or "").lower() in ("name", "nome", "recommender_name") or "nome" in (v.get("label") or "").lower():
                rec_name = v.get("value")
                break
        recs.append({
            "answer_id": ans["id"],
            "name": rec_name, "email": rec_email,
            "date": ans.get("created_at"),
        })
    return recs


def _mapping_tree(db, edict_id, tipo, version):
    m = db.query(Mapping).filter(
        Mapping.edict_id == edict_id, Mapping.type == tipo,
        Mapping.version == str(version)).first()
    return m.tree if m else None


def _accept_info(db, fs, sub):
    if not sub.accept_form_id:
        return {"status": "not_sent"}
    ans = forms_db.get_answer(fs, sub.accept_form_id)
    if not ans:
        return {"status": "sent"}
    values = forms_db.answer_values(fs, sub.accept_form_id)
    info = {"status": "replied" if ans.get("finalized") else "sent", "date": ans.get("created_at")}\n    for v in values:
        n = (v.get("name") or "").lower()
        if "decision" in n or "decision" in (v.get("label") or "").lower():
            info["decision"] = v.get("value")
        if "observation" in n or "observ" in (v.get("label") or "").lower():
            info["observations"] = v.get("value")
        if n == "date" or "data" in (v.get("label") or "").lower():
            info["date"] = v.get("value")
    return info


def _advisor_names(db, sub):
    out = []
    for uid in sub.advisors or []:
        u = db.get(User, uid)
        if u:
            out.append({"id": u.id, "name": u.name, "email": u.email})
    return out


def _summary(db, fs, sub, user):
    edict = db.get(Edict, sub.edict_id)
    values = _answer_values_map(fs, sub.answer_id)
    tree = _mapping_tree(db, sub.edict_id, "candidates", sub.form_version)
    summary = _eval_tree(tree, values) if tree else {}
    fav = db.query(Favorite).filter(
        Favorite.submission_id == sub.id, Favorite.user_id == user.id).first()
    labels = db.query(Label).filter(
        Label.submission_id == sub.id, Label.user_id == user.id).all()
    note = db.get(PrivateNote, (sub.id, user.id))
    bidding = db.get(Bidding, (sub.id, user.id))
    summary.update({
        "id": sub.id,
        "email": _candidate_email(fs, sub.answer_id),
        "stats": sub.stats,
        "favorite": bool(fav),
        "labels": [l.label for l in labels],
        "bidding": bidding.bidding if bidding else "",
        "private_note": note.note if note else "",
        "advisors": _advisor_names(db, sub),
        "entry_semester": sub.entry_semester,
        "letter_sent": sub.letter_sent,
        "accept": _accept_info(db, fs, sub),
        "recommendations": _recommendations(db, fs, edict, sub),
        "edict_id": sub.edict_id,
    })
    return summary


def _submission_item(db, fs, sub, user):
    item = _summary(db, fs, sub, user)
    item["recommendations_count"] = len(item.get("recommendations") or [])
    return item


@router.get("/edicts/{edict_id}/submissions")
def list_submissions(edict_id: str, stats: str | None = None,
                     only_favorites: bool = False,
                     user=Depends(current_user), db=Depends(get_db), fs=Depends(get_forms_db)):
    edict = db.get(Edict, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    subs = db.query(Submission).filter(Submission.edict_id == edict_id).all()
    if stats is not None:
        subs = [s for s in subs if s.stats == stats]
    if only_favorites:
        favs = {f.submission_id for f in db.query(Favorite).filter(Favorite.user_id == user.id).all()}
        subs = [s for s in subs if s.id in favs]
    return {"submissions": [_submission_item(db, fs, s, user) for s in subs]}


@router.get("/submissions/{submission_id}")
def get_submission(submission_id: str, include_comments: bool = False,
                    user=Depends(current_user), db=Depends(get_db), fs=Depends(get_forms_db)):
    sub = _get_sub(db, submission_id)
    summary = _summary(db, fs, sub, user)
    # todas as seções e campos da resposta, inclusive não mapeados
    ans = forms_db.get_answer(fs, sub.answer_id)
    sections = forms_db.select_sections(
        fs, ans["form_id"] if ans else "", sub.form_version)
    values = {(str(r["section_id"]), str(r["field_id"])): r for r in _flat_values(fs, sub.answer_id)}
    submission_form = []
    for s in sections:
        fields = []
        for f in forms_db.section_fields(fs, s["id"]):
            v = values.get((str(s["id"]), str(f["id"])))
            fields.append({
                "id": f["id"], "name": f["name"], "label": f["label"],
                "type": f["type"], "prefix": f.get("prefix"),
                "position": f["position"],
                "value": v.get("value") if v else None,
            })
        submission_form.append({
            "id": s["id"], "name": s["name"], "label": s.get("label"),
            "position": s["position"], "fields": fields,
        })
    out = {"summary": summary, "submission_form": submission_form}
    if include_comments:
        out["comments"] = _activity(db, fs, sub)
    return out


# ---------------------------------------------------------------------- anexos

@router.get("/submissions/{submission_id}/files/{label}/{filename}")
def download_file(submission_id: str, label: str, filename: str,
                   user=Depends(current_user), db=Depends(get_db), fs=Depends(get_forms_db)):
    sub = _get_sub(db, submission_id)
    target = None
    for row in forms_db.answer_values(fs, sub.answer_id):
        if str(row["name"]) == str(label) or str(row["label"]) == str(label):
            if str(row["value"]) == str(filename):
                target = str(row["value"])
                break
    if target is None:
        raise HTTPException(status_code=404, detail="File not found")
    for root, _, files in os.walk(settings.UPLOADS_DIR):
        if target in files:
            path = os.path.join(root, target)
            return FileResponse(
                path, media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{target}"'})
    raise HTTPException(status_code=404, detail="File not found")


# ------------------------------------------------------------------ comentários


def _activity(db, fs, sub):
    events = [{
        "type": "submission", "user": _candidate_email(fs, sub.answer_id),
        "text": "", "date": sub.created_at,
    }]
    edict = db.get(Edict, sub.edict_id)
    for rec in _recommendations(db, fs, edict, sub):
        events.append({"type": "recommendation", "user": rec["email"],
                       "text": "", "date": rec["date"]})
    if sub.accept_form_id:
        ans = forms_db.get_answer(fs, sub.accept_form_id)
        if ans:
            events.append({"type": "accept", "user": ans.get("email"),
                           "text": "", "date": ans.get("created_at")})
    for c in db.query(Comment).filter(Comment.submission_id == sub.id).all():
        u = db.get(User, c.user_id)
        events.append({
            "type": "comment", "user": u.email if u else c.user_id,
            "text": c.comment, "date": c.created_at,
        })
    events.sort(key=lambda e: e["date"] or datetime.min)
    return events


@router.post("/submissions/{submission_id}/comments")
def create_comment(submission_id: str, body: dict = Body(...),
                   user=Depends(current_user), db=Depends(get_db)):
    sub = _get_sub(db, submission_id)
    _require_phase(db, sub, "avaliacao")
    created_at = body.get("created_at")
    if created_at:
        created_at = datetime.fromisoformat(str(created_at))
    c = Comment(submission_id=sub.id, user_id=user.id,
                comment=body.get("comment", ""), created_at=created_at)
    db.add(c)
    db.commit()
    return {
        "id": c.id, "user_id": c.user_id, "submission_id": c.submission_id,
        "comment": c.comment, "created_at": c.created_at, "updated_at": c.updated_at,
    }


@router.get("/submissions/{submission_id}/comments")
def get_comments(submission_id: str, user=Depends(current_user),
                  db=Depends(get_db), fs=Depends(get_forms_db)):
    sub = _get_sub(db, submission_id)
    return _activity(db, fs, sub)


@router.delete("/submissions/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: str, user=Depends(current_user), db=Depends(get_db)):
    c = db.get(Comment, comment_id)
    if not c:
        raise HTTPException(status_code=404, detail="Comment not found")
    if c.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(c)
    db.commit()


# -------------------------------------------------------------------- favoritos


@router.post("/submissions/{submission_id}/favorites", status_code=201)
def add_favorite(submission_id: str, user=Depends(current_user), db=Depends(get_db)):
    sub = _get_sub(db, submission_id)
    _require_phase(db, sub, "avaliacao")
    existing = db.get(Favorite, (sub.id, user.id))
    if existing:
        raise HTTPException(status_code=409, detail="Already favorited")
    db.add(Favorite(submission_id=sub.id, user_id=user.id))
    db.commit()
    return {"message": "Favorite added"}


@router.delete("/submissions/{submission_id}/favorites", status_code=204)
def remove_favorite(submission_id: str, user=Depends(current_user), db=Depends(get_db)):
    sub = _get_sub(db, submission_id)
    fav = db.get(Favorite, (sub.id, user.id))
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    db.commit()


# --------------------------------------------------------------------- etiquetas


@router.post("/submissions/{submission_id}/labels")
def create_label(submission_id: str, body: dict = Body(...),
                  user=Depends(current_user), db=Depends(get_db)):
    sub = _get_sub(db, submission_id)
    _require_phase(db, sub, "avaliacao")
    label = str(body.get("label", ""))
    color = str(body.get("color", ""))
    existing = db.query(Label).filter(
        Label.submission_id == sub.id, Label.user_id == user.id,
        Label.label == label).first()
    if existing:
        existing.color = color
    else:
        existing = Label(submission_id=sub.id, user_id=user.id,
                          label=label, color=color, context="candidate")
        db.add(existing)
    db.flush()
    # atualiza a cor das etiquetas do mesmo autor e rótulo em outras inscrições,
    # preservando os demais autores e o contexto de interesses (bidding)
    for l in db.query(Label).filter(
            Label.user_id == user.id, Label.label == label,
            Label.context == "candidate").all():
        l.color = color
    db.commit()
    return {"id": existing.id, "user_id": user.id,
            "submission_id": sub.id, "label": label, "color": color}


@router.get("/submissions/{submission_id}/labels")
def list_labels(submission_id: str, user=Depends(current_user), db=Depends(get_db)):
    _get_sub(db, submission_id)
    labels = db.query(Label).filter(Label.user_id == user.id).all()
    seen, out = set(), []
    for l in labels:
        if l.label not in seen:
            seen.add(l.label)
            out.append({"id": l.id, "label": l.label, "color": l.color})
    return out


@router.delete("/submissions/label/{label_id}", status_code=204)
def delete_label(label_id: str, user=Depends(current_user), db=Depends(get_db)):
    l = db.get(Label, label_id)
    if not l:
        raise HTTPException(status_code=404, detail="Label not found")
    if l.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(l)
    db.commit()


# ------------------------------------------------------------------ notas privadas


@router.post("/submissions/{submission_id}/private_notes")
def set_private_note(submission_id: str, body: dict = Body(...),
                     user=Depends(current_user), db=Depends(get_db)):
    sub = _get_sub(db, submission_id)
    _require_phase(db, sub, "avaliacao")
    note = db.get(PrivateNote, (sub.id, user.id))
    text = str(body.get("note", ""))
    if note:
        note.note = text
    else:
        db.add(PrivateNote(submission_id=sub.id, user_id=user.id, note=text))
    db.commit()
    return {"note": text}


# -------------------------------------------------------------------- visualizações


@router.post("/submissions/{submission_id}/view")
def register_view(submission_id: str, user=Depends(current_user), db=Depends(get_db)):
    sub = _get_sub(db, submission_id)
    today = datetime.now(TZ).date()
    existing = db.query(View).filter(
        View.submission_id == sub.id, View.user_id == user.id,
        View.date == today).first()
    if not existing:
        db.add(View(submission_id=sub.id, user_id=user.id, date=today))
        db.commit()
    return {"message": "View registered"}


@router.get("/submissions/{submission_id}/view")
def list_views(submission_id: str, user=Depends(current_user), db=Depends(get_db)):
    sub = _get_sub(db, submission_id)
    views = db.query(View).filter(View.submission_id == sub.id).all()
    return [{"user_id": v.user_id, "date": v.date.isoformat()} for v in views]


# ------------------------------------------------------------------- interesses


@router.post("/submissions/{submission_id}/bidding")
def set_bidding(submission_id: str, body: dict = Body(...),
                user=Depends(current_user), db=Depends(get_db)):
    sub = _get_sub(db, submission_id)
    bidding = str(body.get("bidding", ""))
    if bidding not in BIDDING_VALUES:
        raise HTTPException(status_code=422, detail="Invalid bidding")
    target_id = body.get("user_id")
    if target_id:
        if user.role not in ADMIN_ROLES:
            target_id = user.id
    else:
        target_id = user.id
    if not db.get(User, target_id):
        raise HTTPException(status_code=404, detail="User not found")
    b = db.get(Bidding, (sub.id, target_id))
    if b:
        b.bidding = bidding
    else:
        db.add(Bidding(submission_id=sub.id, user_id=target_id, bidding=bidding))
    db.commit()
    return {"bidding": bidding, "user_id": target_id}


# ------------------------------------------------------------- seleção e semestre


@router.post("/submissions/{submission_id}/select")
def select_submission(submission_id: str, body: dict = Body(...),
                      user=Depends(current_user), db=Depends(get_db)):
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Forbidden")
    sub = _get_sub(db, submission_id)
    edict = db.get(Edict, sub.edict_id)
    if not edict.is_open:
        raise HTTPException(status_code=409, detail="Edict is closed")
    stats = body.get("stats")
    if stats not in STATS_VALUES:
        raise HTTPException(status_code=422, detail="Invalid stats")
    user_ids = body.get("user_ids")
    if stats == "approved":
        if not user_ids or len(user_ids) != 1:
            raise HTTPException(status_code=400, detail="Approved requires exactly one advisor")
        if not db.get(User, user_ids[0]):
            raise HTTPException(status_code=400, detail="Advisor not found")
        sub.advisors = user_ids
    sub.stats = stats
    db.commit()
    return {"stats": sub.stats, "advisors": _advisor_names(db, sub)}


@router.post("/submissions/{submission_id}/entry-semester")
def set_entry_semester(submission_id: str, body: dict = Body(...),
                        user=Depends(current_user), db=Depends(get_db)):
    sub = _get_sub(db, submission_id)
    semester = str(body.get("semester", ""))
    sub.entry_semester = SEMESTER_MAP.get(semester.strip().lower(), semester)
    db.commit()
    return {"semester": sub.entry_semester}


# ------------------------------------------------------------- correção e aceite


@router.post("/submissions/{submission_id}/reesend_submission")
def resend_submission(submission_id: str, body: dict = Body(...),
                      user=Depends(current_user), db=Depends(get_db), fs=Depends(get_forms_db)):
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Forbidden")
    sub = _get_sub(db, submission_id)
    _require_phase(db, sub, "homologacao")
    text = str(body.get("text", ""))
    # reabre a resposta de candidatura no Forms, com seção atual zero
    forms_db.reopen_answer(fs, sub.answer_id)
    share = forms_db.share_for_answer(fs, sub.answer_id) or forms_db.create_share(
        fs, sub.answer_id, _candidate_email(fs, sub.answer_id))
    link = f"{settings.BASE_URL.rstrip('/')}/form/{share['token']}"
    email = _candidate_email(fs, sub.answer_id)
    html = (
        f"<p>Prezado(a) candidato(a),</p>"
        f"<p>Sua inscrição precisa de correção.</p>"
        f"<p>Motivo: {text}</p>"
        f"<p>Para corrigir e reenviar, acesse: <a href='{link}'>{link}</a></p>"
    )
    sent = send_mail("Correção de inscrição", [email] if email else [],
                     html, bcc=[user.email])
    return {"message": "Submission reopened", "email_sent": sent}


@router.post("/submissions/{submission_id}/send-accept")
def send_accept(submission_id: str, user=Depends(current_user),
                db=Depends(get_db), fs=Depends(get_forms_db)):
    sub = _get_sub(db, submission_id)
    edict = db.get(Edict, sub.edict_id)
    if not edict.accept_form_id:
        raise HTTPException(status_code=404, detail="Accept form not configured")
    if sub.stats != "approved":
        raise HTTPException(status_code=400, detail="Submission not approved")
    if sub.accept_form_id:
        raise HTTPException(status_code=400, detail="Accept already sent")
    email = _candidate_email(fs, sub.answer_id)
    answer_id = forms_db.create_answer(fs, edict.accept_form_id, email)
    forms_db.create_share(fs, answer_id, email, expires=edict.date_closed, single=True)
    sub.accept_form_id = str(answer_id)
    db.commit()
    share = forms_db.share_for_answer(fs, answer_id)
    link = f"{settings.BASE_URL.rstrip('/')}/form/{share['token']}"
    advisor = _advisor_names(db, sub)
    advisor_email = advisor[0]["email"] if advisor else None
    deadline = edict.date_closed.strftime("%d/%m/%Y") if edict.date_closed else ""
    name = ""
    for k, v in (_summary(db, fs, sub, user).items()):
        if k in ("name", "nome", "candidate_name") and v:
            name = str(v)
            break
    html = (
        f"<p>Prezado(a) {name},</p>"
        f"<p>Parabéns pela aprovação! Preencha o formulário de aceite até {deadline}:</p>"
        f"<p><a href='{link}'>{link}</a></p>"
        f"<p>Dear {name}, congratulations! Please fill the acceptance form by {deadline}:</p>"
        f"<p><a href='{link}'>{link}</a></p>"
    )
    sent = send_mail("Formulário de aceite / Acceptance form", [email] if email else [],
                     html, cc=[advisor_email] if advisor_email else None)
    return {"message": "Accept form sent", "email_sent": sent}


@router.post("/submissions/{submission_id}/send-letter")
def send_letter(submission_id: str, user=Depends(current_user),
                db=Depends(get_db), fs=Depends(get_forms_db)):
    sub = _get_sub(db, submission_id)
    if sub.stats != "approved":
        raise HTTPException(status_code=400, detail="Submission not approved")
    if sub.letter_sent:
        raise HTTPException(status_code=400, detail="Letter already sent")
    edict = db.get(Edict, sub.edict_id)
    email = _candidate_email(fs, sub.answer_id)
    summary = _summary(db, fs, sub, user)
    name = str(summary.get("name") or summary.get("nome") or "")
    advisor = _advisor_names(db, sub)
    advisor_email = advisor[0]["email"] if advisor else None
    semester = sub.entry_semester or ""
    signature = ""
    if os.path.exists(settings.SIGNATURE_FILE):
        with open(settings.SIGNATURE_FILE) as f:
            signature = f.read()
    html = (
        f"<h2>Carta de Aprovação</h2>"
        f"<p>Prezado(a) <b>{name}</b>,</p>"
        f"<p>Informamos que sua candidatura foi aprovada no edital {edict.title}.</p>"
        f"<p>Orientador(a): <b>{advisor[0]['name'] if advisor else ''}</b></p>"
        f"<p>Semestre de ingresso: <b>{semester}</b></p>"
        f"<p>Ano de ingresso: <b>{edict.year}</b></p>"
        f"{signature}"
    )
    sent = send_mail("Carta de Aprovação / Approval Letter", [email] if email else [],
                     html, cc=[advisor_email] if advisor_email else None)
    sub.letter_sent = True
    db.commit()
    return {"message": "Letter sent", "email_sent": sent}
