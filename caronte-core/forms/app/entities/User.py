from typing import TypedDict, NewType

class User(TypedDict):
    email: str
    role: str

UserType = NewType('UserType', User)