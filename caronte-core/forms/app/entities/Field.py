from typing import List, TypedDict, NewType
from enum import Enum

from .Options import Options


# Must mirror typeRegistry in static-assets/scripts/components/FormBuilder/schema-config.js
class FieldTypeEnum(str, Enum):
    TEXT = "Text"
    LONGTEXT = "LongText"
    NUMBER = "Number"
    FILE = "File"
    DATE = "Date"
    CHECKBOX = "CheckBox"
    RADIO = "Radio"


class Field(TypedDict):
    label: dict
    name: str
    type: str
    placeholder: str
    required: bool
    disabled: bool
    description: dict
    options: List[Options]
    validation: str
    prefix: str
    error_message: dict
    version: int
    is_active: (
        bool  # para retrocompatibilidade, ter-se-ão as seções antigas no banco de dados
    )


FieldType = NewType("FieldType", Field)
