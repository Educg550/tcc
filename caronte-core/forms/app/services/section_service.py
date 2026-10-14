import json
from app.common.Result import Result
from app.exceptions.error_messages import INVALID_INPUT
from app.extension import get_locale
from app.repositories.form_repository import get_partial_form_dict_raw
from app.services.entry_service import decode_entry
from app.services.response_service import get_partial_response


def get_fields_by_section(db, form_id, section_id, lang="") -> Result:
    fields = get_partial_form_dict_raw(db, form_id, section_id, lang)

    if fields is None:
        return Result([])

    return Result(fields)


def get_section_by_id(db, id) -> Result:
    sql_string = """
        select id, title from form_section
        where form_id = %s and is_active = true order by position
    """

    res = None
    with db.transaction() as f:
        res = f.sql_dict(sql_string, (id,), callback=lambda x: x.fetchall())

    return Result(res)


def load_section_info(db, entry_str, form_id, response_id, current_pos):
    # id section
    sections = get_section_by_id(db, form_id)
    if not sections.succeeded:
        return Result(message="Seção inválida")
    if current_pos < 0 or current_pos > len(sections.data) - 1:
        return Result(message="Seção inválida")
    current_section = sections.data[current_pos]

    # fields section
    section = get_fields_by_section(
        db, form_id, current_section["id"], lang=get_locale()
    )
    if not section.succeeded:
        return Result(message="Seção inválida")

    entry_pos, entry_name = {}, {}
    try:
        entry_pos, entry_name = decode_entry(db, form_id, entry_str)
    except Exception as _:
        return Result(message=INVALID_INPUT())

    field_ids = [field["id"] for field in section.data["fields"]]
    partial_responses = get_partial_response(db, response_id, field_ids)

    for partial_response in partial_responses.data:
        if partial_response["type"] == "CheckBox":
            try:
                checked_options = json.loads(partial_response["value"])
            except Exception:
                checked_options = []

            for i, option in enumerate(checked_options, start=1):
                if (option) and f"{partial_response['position']}_{i}" not in entry_pos:
                    entry_pos[f"{partial_response['position']}_{i}"] = True
        else:
            if (
                partial_response["value"]
                and str(partial_response["position"]) not in entry_pos
            ):
                entry_pos[str(partial_response["position"])] = partial_response["value"]

    return Result(
        {
            "sections": sections.data,
            "section": section.data,
            "partial_responses": partial_responses.data,
            "entry_pos": entry_pos,
            "entry_name": entry_name,
            "current_pos": current_pos,
        }
    )


def set_section(db, response_id, section_pos):
    sql_string = """
    update form_response
        set current_section = %s
        where id = %s
    returning id, current_section;
    """

    res = None
    with db.transaction() as f:
        res = f.sql_dict(
            sql_string,
            (
                section_pos,
                response_id,
            ),
            callback=lambda x: x.fetchone(),
        )

    return Result(res)
