from fastapi import HTTPException


def validate_tree(tree, sections: set, fields: set) -> None:
    """Valida referências de seção/campo em uma árvore de mapeamento arbitrária."""
    if tree is None:
        return
    if not isinstance(tree, dict):
        raise HTTPException(status_code=422, detail='Árvore de mapeamento inválida')
    for value in tree.values():
        if value is None:
            continue
        if not isinstance(value, dict):
            raise HTTPException(status_code=422, detail='Folha de mapeamento inválida')
        if 'section' in value and 'field' in value:
            if (not isinstance(value['section'], int)
                    or not isinstance(value['field'], int)):
                raise HTTPException(status_code=422, detail='Folha de mapeamento inválida')
            if (value['section'] not in sections
                    or (value['field'], value['section']) not in fields):
                raise HTTPException(
                    status_code=422,
                    detail=f"Seção/campo inexistente: {value['section']}/{value['field']}")
        else:
            validate_tree(value, sections, fields)


def walk_tree(tree, values: dict) -> dict:
    out = {}
    if not isinstance(tree, dict):
        return out
    for key, value in tree.items():
        if isinstance(value, dict) and 'field' in value and 'section' in value:
            out[key] = values.get(value['field'])
        elif isinstance(value, dict):
            out[key] = walk_tree(value, values)
        else:
            out[key] = None
    return out
