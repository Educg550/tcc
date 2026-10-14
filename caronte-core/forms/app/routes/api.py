from app.exceptions.error_messages import FORM_NOT_FOUND
from app.extension import get_locale
from flask import Blueprint, abort, current_app
from app.common import remove_null_values, to_csv
import json

from app.config import load_config
from app.services.collaborator_service import can_access_form

from app.middleware import require_authorization
from app.services.form_service import (
    get_all_user_forms,
    get_all_submissions_dict,
    get_form_dict,
)
from app.persistence.db import db

config = load_config()
api = Blueprint("api", __name__, url_prefix="/<lang_code>/api")


@api.route("/admin/logs")
@require_authorization(role="administrator")
def logs(user):
    def generate():
        with open("logs/app.log") as f:
            while True:
                line = f.readline()
                if not line:
                    break

                yield line

    return current_app.response_class(generate(), mimetype="text/plain")


@api.route("/form")
@require_authorization()
def forms(user):
    order_by = 1
    order_type = 0

    list_forms = get_all_user_forms(
        db, user, order_by, order_type, {}, lang=get_locale()
    )

    output = to_csv(list_forms)

    return current_app.response_class(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=forms.csv"},
    )


@api.route("/form/viewer/<int:id>")
@require_authorization()
def viewer(user, id):
    can_access = can_access_form(db, user, id)
    if not can_access.succeeded or not can_access.data:
        abort(401, FORM_NOT_FOUND())

    res = get_form_dict(db, id)
    res.data = remove_null_values(res.data)

    output = json.dumps(
        res.data, default=str, indent=4, ensure_ascii=False, allow_nan=False
    )

    return current_app.response_class(
        output,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=form_schema.json"},
    )


@api.route("/form/submissions/<int:id>")
@require_authorization()
def submissions(user, id):
    can_access = can_access_form(db, user, id)
    if not can_access.succeeded or not can_access.data:
        abort(401, FORM_NOT_FOUND())

    order_by = 1
    order_type = 0

    list_submissions = get_all_submissions_dict(db, id, order_by, order_type)

    for data in list_submissions.data:
        for response in data["responses"]:
            response = {f"r-{k}": v["value"] for k, v in response.items()}
            data.update(response)
        del data["responses"]

    output = to_csv(list_submissions)

    return current_app.response_class(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=submissions.csv"},
    )


@api.errorhandler(404)
def page_not_found(error):
    return "404", 404


@api.errorhandler(401)
def unauthorized(error):
    return "401", 401
