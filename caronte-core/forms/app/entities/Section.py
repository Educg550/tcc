from typing import List, TypedDict, NewType

from app.entities.Field import Field

class Section(TypedDict):
    title: dict
    description: dict
    position: int
    version: int
    is_active: bool
    fields: List[Field]

SectionType = NewType('SectionType', Section)
