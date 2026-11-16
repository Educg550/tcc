def iter_leaves(tree, path=()):
    if not isinstance(tree, dict):
        return
    for key, value in tree.items():
        if isinstance(value, dict) and "section" in value and "field" in value:
            yield path + (key,), value
        elif isinstance(value, dict):
            yield from iter_leaves(value, path + (key,))
        elif value is None:
            yield path + (key,), None


def _find_by_key(tree, key):
    if not isinstance(tree, dict):
        return None
    for k, value in tree.items():
        if k == key:
            return value
    for value in tree.values():
        if isinstance(value, dict) and "section" not in value:
            found = _find_by_key(value, key)
            if found is not None:
                return found
    return None


def resolve_leaf(tree, path):
    """Resolve a mapping path like ("personal", "name") to a leaf.

    Falls back to a global search by the last key when the parent path
    does not exist in the tree.
    """
    node = tree
    for part in path[:-1]:
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            node = None
            break
    if isinstance(node, dict) and path[-1] in node:
        return node[path[-1]]
    return _find_by_key(tree, path[-1])


def resolve_value(tree, path, values: dict):
    leaf = resolve_leaf(tree, path)
    if not isinstance(leaf, dict):
        return None
    return values.get(leaf.get("field"))


def collect_leaf_refs(tree):
    refs = []
    for _path, leaf in iter_leaves(tree):
        if isinstance(leaf, dict):
            refs.append((leaf.get("section"), leaf.get("field")))
    return refs
