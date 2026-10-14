from http import HTTPStatus
from fastapi import HTTPException


class SubmissionNotFound(HTTPException):
    def __init__(self, submission_id: int):
        self.status_code = HTTPStatus.NOT_FOUND
        self.detail = f"Submission with ID {submission_id} was not found."

class AcceptFormsNotFound(HTTPException):
    def __init__(self):
        self.status_code = HTTPStatus.NOT_FOUND
        self.detail = "Accept Forms was not found."


class AcceptFormsAlreadyCreated(HTTPException):
    def __init__(self):
        self.status_code = HTTPStatus.BAD_REQUEST
        self.detail = "Form already created and submitted."

class AllowedOnlyForApprovedCandidates(HTTPException):
    def __init__(self):
        self.status_code = HTTPStatus.BAD_REQUEST
        self.detail = "Allowed only for approved candidates."

class EmailAlreadySent(HTTPException):
    def __init__(self):
        self.status_code = HTTPStatus.BAD_REQUEST
        self.detail = "Email already sent."

class UserNotFound(HTTPException):
    def __init__(self, user_id: int):
        self.status_code = HTTPStatus.BAD_REQUEST
        self.detail = f"User with ID {user_id} was not found and cannot be attributed to this request."

class EdictNotFound(HTTPException):
    def __init__(self, edict_id: int):
        self.status_code = HTTPStatus.BAD_REQUEST
        self.detail = f"Edict with ID {edict_id} was not found."


class UncheckingOneselfAsAdvisor(HTTPException):
    def __init__(self, user_id: int):
        self.status_code = HTTPStatus.BAD_REQUEST
        self.detail = "It is not possible to deselect interest if the candidate has already been approved."

class FavoriteAlreadyExists(HTTPException):
    def __init__(self, user_id: int, submission_id: int):
        super().__init__(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Favorite for User ID {user_id} and Submission ID {submission_id} already exists."
        )

class FavoriteNotFound(Exception):
    def __init__(self, user_id: int, submission_id: int):
        self.user_id = user_id
        self.submission_id = submission_id
        self.message = f"Favorite with User ID {user_id} and Submission ID {submission_id} not found."
        super().__init__(self.message)


class CommentNotFound(HTTPException):
    def __init__(self, comment_id):
        self.status_code = HTTPStatus.NOT_FOUND
        self.detail = f"Comment with id {comment_id} was not found."


class CommentFromAnotherUser(HTTPException):
    def __init__(self, comment_id):
        self.status_code = HTTPStatus.FORBIDDEN
        self.detail = f"Comment with id {comment_id} was made by another user, so it can't be deleted by you."

class SubmissionNoInterest(HTTPException):
    def __init__(self, submission_id: int):
        self.status_code = HTTPStatus.BAD_REQUEST
        self.detail = f"Submission with ID {submission_id} has no interested users and cannot be approved."

class MultiplesAdvisors(HTTPException):
    def __init__(self, submission_id: int):
        self.status_code = HTTPStatus.CONFLICT
        self.detail = "Sent multiple advisors."

class EdictClosed(HTTPException):
    def __init__(self, edict_id: int):
        self.status_code = HTTPStatus.CONFLICT
        self.detail = f"Edict with ID {edict_id} is already closed and the approval cannot be altered."

class IncorrectActionInPphase(HTTPException):
    def __init__(self, action: str, phase: str):
        self.status_code = HTTPStatus.BAD_REQUEST
        self.detail = f'Action of \"{action}\" carried out in the \"{phase}\" phase.'