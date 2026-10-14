from typing import TypedDict, NewType

class Response(TypedDict):
    response_id: int
    field_id: int
    value: str

ResponseType = NewType('ResponseType', Response)