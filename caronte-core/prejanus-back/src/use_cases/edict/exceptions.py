from fastapi import HTTPException


class AlreadyClosedEdict(HTTPException):
    def __init__(self):
        self.status_code = 409
        self.detail = "The operation cannot be completed because the edict is already closed."

class SlotsTyping(HTTPException):
    def __init__(self):
        self.status_code = 500
        self.detail = "Cannot convert non-numeric string to integer."
