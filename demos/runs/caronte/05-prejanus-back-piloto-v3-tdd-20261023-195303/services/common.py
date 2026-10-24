from sqlalchemy import text


def get_edict(ps, edict_id):
    return ps.execute(text("select * from edict where id=:i"), {"i": edict_id}).mappings().first()


def get_submission(ps, submission_id):
    return ps.execute(text("select * from submission where id=:i"), {"i": submission_id}).mappings().first()


def get_user_row(ps, user_id):
    return ps.execute(text('select * from "user" where id=:i'), {"i": user_id}).mappings().first()


def user_brief(row):
    if row is None:
        return None
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def parse_form_ids(value):
    if not value:
        return []
    out = []
    for part in str(value).replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            out.append(int(part))
    return out
