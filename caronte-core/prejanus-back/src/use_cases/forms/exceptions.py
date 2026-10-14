from http import HTTPStatus
from fastapi import HTTPException


class FormNotFound(HTTPException):
    def __init__(self, edict_id: int):
        self.status_code = HTTPStatus.BAD_REQUEST
        self.detail = f"Form with ID {edict_id} was not found."
