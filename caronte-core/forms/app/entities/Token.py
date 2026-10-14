import datetime
from typing import TypedDict, NewType

class Token(TypedDict):
    form_id: int
    unique_answers: bool
    created_at: datetime.datetime
    expiration_at: datetime.datetime
    is_public: bool
    token: str

TokenType = NewType('TokenType', Token)