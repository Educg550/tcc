import base64
from app.services.field_service import get_field_by_name, get_field_by_position


# TODO: encode using secret key
def create_entry_str(db, form_id, entry_list):
    for entry in entry_list:
        field = get_field_by_name(db, form_id, entry["name"])
        if not field.succeeded:
            continue
        entry["position"] = field.data["position"]

    entry_str = ""
    for entry in entry_list:
        if "position" not in entry:
            continue
        entry_str += f"{entry['position']}={entry['value']}&"
    entry_str = base64.urlsafe_b64encode(entry_str.encode("UTF-8"))
    return entry_str


def decode_entry(db, form_id, entry_str):
    entry_position = {}
    if entry_str:
        parts = base64.urlsafe_b64decode(entry_str).decode("UTF-8").split("&")
        for part in parts:
            seq = part.split("=")
            if len(seq) > 1 and seq[1]:
                entry_position[str(seq[0])] = seq[1]

    entry_name = {}
    for position, value in entry_position.items():
        field = get_field_by_position(db, form_id, position)
        if not field.succeeded:
            continue
        entry_name[field.data["name"]] = value

    return entry_position, entry_name
