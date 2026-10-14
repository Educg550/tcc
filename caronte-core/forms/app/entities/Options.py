from typing import TypedDict, NewType

class Options(TypedDict):
    field_id: int
    value: dict
    metadata: str

OptionsType = NewType('OptionsType', Options)