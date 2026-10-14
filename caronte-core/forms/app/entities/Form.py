import datetime
from enum import Enum
from typing import List, TypedDict, NewType

from app.entities.Section import Section

class FormPhaseEnum(str, Enum):
    REGISTRATION = 'Registration',
    APPROVAL = 'Approval',
    COMPLETED = 'Completed'

class Form(TypedDict):
    title: dict
    description: dict
    version: int
    created_at: datetime.datetime
    created_by: int
    sections: List[Section]
    tags: dict
    phase: str
    metadata: dict

FormType = NewType('FormType', Form)
