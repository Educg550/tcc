
from fastapi import HTTPException, status


class UserNotAuthenticatedInSenhaunica(HTTPException):
    def __init__(self):
        self.status_code = status.HTTP_401_UNAUTHORIZED
        self.detail = "The user is not logged in or the credentials are invalid."