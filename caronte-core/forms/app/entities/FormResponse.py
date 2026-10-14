import datetime
from typing import List, TypedDict, NewType
from .Response import Response

class FormResponse(TypedDict):
    form_id: int
    shared_id: int
    user_id: int
    form_version: int
    submitted_at: datetime.datetime
    metadata: str
    email: str
    token: str
    responses: List[Response]

FormResponseType = NewType('FormResponseType', FormResponse)