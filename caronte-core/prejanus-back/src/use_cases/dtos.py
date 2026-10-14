from pydantic import BaseModel


class UserDTO(BaseModel):
    id: int
    email: str
    name: str
    nusp: str
    role: str