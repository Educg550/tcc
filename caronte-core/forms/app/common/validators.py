import re

def is_required_filled(field, responses):
    return not (field.get("required") is True and (field["name"] not in responses or responses.get(field["name"]) == ""))



def is_valid_regex(field, value):
    if not field.get("validation"):
        return True
    
    pattern = re.compile(field["validation"])
    match = bool(pattern.match(value))
    if not match:
        return False
    
    return True

def email_regex():
    return r"[\w\.\-]+@[\dA-z\.\-]+\.[A-z\.]+"
