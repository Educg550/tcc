from fastapi import HTTPException

import services.forms_db as forms_db


def iter_leaves(node):
    if isinstance(node, dict):
        if set(node.keys()) == {"section", "field"}:
            yield node
        else:
            for child in node.values():
                yield from iter_leaves(child)


async def valid_field_ids(form_id: int, version: int) -> set[int]:
    sections = await forms_db.get_sections(form_id, version)
    valid: set[int] = set()
    for section in sections:
        for field in await forms_db.get_fields(section["id"], version):
            valid.add(field["id"])
    if not valid:
        # fallback original: todas as seções do formulário
        sections = await forms_db.get_sections(form_id, None)
        for section in sections:
            for field in await forms_db.get_fields(section["id"], None):
                valid.add(field["id"])
    return valid


async def validate_mapping(form_id: int, version: int, tree: dict) -> None:
    valid = await valid_field_ids(form_id, version)
    for leaf in iter_leaves(tree):
        if leaf["field"] not in valid:
            raise HTTPException(
                status_code=422,
                detail="Referência de campo inválida no mapeamento",
            )


def resolve_mapping(tree, values: dict[int, str]):
    if tree is None:
        return None
    if isinstance(tree, dict) and set(tree.keys()) == {"section", "field"}:
        return values.get(tree["field"])
    if isinstance(tree, dict):
        return {k: resolve_mapping(v, values) for k, v in tree.items()}
    return tree
