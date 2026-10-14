from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from src.use_cases.submission.schemas import (
    GraduationSchema,
    LabelSchema,
    SubmissionApprovalSchema as BaseSubmissionSchema,
    AcceptSchema,
)


class UserSchema(BaseModel):
    id: int
    name: str
    email: str


class CommentSchema(BaseModel):
    user: UserSchema
    id: int
    comment: str
    created_at: datetime
    type: str


class DocumentSchema(BaseModel):
    title: str
    label: str
    url: Optional[str] = None


class RecommenderSchema(BaseModel):
    fullname_candidate: str
    fullname: str
    affiliation: Optional[str] = None
    known_time: Optional[str] = None
    relationship: Optional[list[str]] = None
    rating: Optional[str] = None
    submitted_at: Optional[datetime] = None
    email: Optional[str]
    sent: bool


class SubmissionSchema(BaseSubmissionSchema):
    graduation: GraduationSchema
    documents: list[DocumentSchema]
    comments: list[CommentSchema]
    recommenders: list[RecommenderSchema]
    private_note: str
    stats: str
    user_bidding: str
    about_this_program: str
    relevant_information: str
    labels: list[LabelSchema]
    accept: AcceptSchema
    entry_semester: str
    letter_sent: bool


class GetSubmissionDetailsResponse(SubmissionSchema):
    pass
