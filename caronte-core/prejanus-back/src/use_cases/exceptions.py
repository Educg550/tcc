from http import HTTPStatus
from fastapi import HTTPException


class InsufficientRole(HTTPException):
    def __init__(self):
        self.status_code = HTTPStatus.FORBIDDEN
        self.detail = "Insufficient role."


class InvalidMappingError(Exception):
    def __init__(self, path: str):
        super().__init__(f'O campo "{path}" do mapeamento não foi configurado.')
        self.path = path
