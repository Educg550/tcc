from typing import Any, Dict, Union, Optional, cast
from src.use_cases.exceptions import InvalidMappingError
import json

MappingLeaf = Dict[str, Optional[int]]
MappingNode = Dict[str, Union["MappingNode", MappingLeaf, None]]


def build_lookup(responses):
    lookup = {}
    for section in responses:
        for field in section["fields"]:
            key = f'{field["section_id"]}:{field["field_id"]}'
            lookup[key] = field
    return lookup


def parse_value(field):
    if field is None:
        return None

    value = field.get("value")
    field_type = field.get("type")

    if value is None or value == "":
        return None

    try:
        if field_type == "Number":
            return int(value)

        if field_type == "CheckBox":
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []

        if field_type == "Date":
            return value  # manter string ISO

        return value
    except Exception:
        return value


def resolve_node(node: MappingNode, lookup: Dict[str, Any]):
    result = {}

    for key, value in node.items():
        if value is None:
            result[key] = None
            continue

        # Folha
        if isinstance(value, dict) and "section" in value and "field" in value:
            section = value["section"]
            field = value["field"]

            if section is None and field is None:
                result[key] = None
                continue

            if section is None or field is None:
                result[key] = None
                continue

            lookup_key = f"{section}:{field}"
            field_data = lookup.get(lookup_key)
            result[key] = parse_value(field_data)
        else:
            # Nó (recursivo)
            # Uso do cast para uma tipagem coerente
            result[key] = resolve_node(cast(MappingNode, value), lookup)

    return result


def resolve_mapping(node, lookup, path=""):
    if node is None:
        return None

    # Folha
    if isinstance(node, dict) and "section" in node and "field" in node:
        section = node["section"]
        field = node["field"]

        if section is None and field is None:
            raise InvalidMappingError(path)

        if section is None or field is None:
            return None

        key = f"{section}:{field}"
        field_data = lookup.get(key)

        if not field_data:
            return None

        value = field_data.get("value")
        field_type = field_data.get("type")

        if value in (None, ""):
            return None

        if field_type == "Number":
            try:
                return int(value)
            except Exception:
                return value

        if field_type == "CheckBox":
            try:
                if isinstance(value, (list, dict)):
                    return value
                return json.loads(value)
            except Exception:
                return []

        return value

    # Nó
    if isinstance(node, dict):
        return {
            k: resolve_mapping(v, lookup, f"{path}.{k}" if path else k)
            for k, v in node.items()
        }

    # Valor primitivo
    return node


def check_mapping(node, lookup):
    if node is None:
        return True

    # Folha
    if isinstance(node, dict) and "section" in node and "field" in node:
        section = node["section"]
        field = node["field"]

        # Folha não mapeada
        if section is None and field is None:
            return True

        # Apenas um dos dois preenchido
        if section is None or field is None:
            return False

        key = f"{section}:{field}"
        return key in lookup

    # Nó recursivo
    if isinstance(node, dict):
        return all(check_mapping(v, lookup) for v in node.values())

    # Valor inválido
    return False
