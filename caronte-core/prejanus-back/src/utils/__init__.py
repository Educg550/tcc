from distutils.util import strtobool

from src.infra.database.models.user import RolesEnum

def str_for_bool(value):
    if not isinstance(value, str):
        return value
    processed_value = value.strip().lower()
    traducao = {"sim": "yes", "não": "no", "nao": "no"}
    if (processed_value in traducao):
        processed_value = traducao.get(processed_value, processed_value)
    try:
        return bool(strtobool(processed_value))
    except ValueError:
        return value

def is_admin_role(role):
    return role in [ RolesEnum.ADMINISTRATOR.value, RolesEnum.SECRETARY.value, RolesEnum.COORDINATOR.value ]


def get_value(_dict, name, default_value = None):
    if name not in _dict:
        return default_value
    else:
        label=_dict.get(name)
        if label is None:
            return default_value
        else:
            return label
def flatten_responses(responses):
    return {k: v for d in responses for k, v in d.items()}
