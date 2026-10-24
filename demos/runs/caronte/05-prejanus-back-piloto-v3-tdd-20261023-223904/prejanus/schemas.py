from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel


class InsertEdictSchema(BaseModel):
    title: str
    description: Optional[str] = None
    year: int
    semester: int
    edict_type: str
    is_open: bool
    candidate_forms: int
    recommenders_forms: int
    date_application: datetime
    date_evaluation: datetime
    date_verification: datetime
    date_closed: datetime


class EditEdictSchema(BaseModel):
    title: str
    description: str
    year: str
    semester: str
    edict_type: str
    date_application: datetime
    date_evaluation: datetime
    date_verification: datetime
    date_closed: datetime


class EditEdictDateSchema(BaseModel):
    closed_date: date


class AdvancePhaseEdictSchema(BaseModel):
    id: int


class CloseEdictSchema(BaseModel):
    confirmation_deadline: date
    send_approval_letter: bool


class SlotsSchema(BaseModel):
    amount: str


class CommentSchema(BaseModel):
    comment: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LabelInputSchema(BaseModel):
    label: str
    color: str


class PrivateNoteSchema(BaseModel):
    note: str


class RequestReesendSchema(BaseModel):
    text: str


BiddingEnum = Literal[
    "decline", "available", "interested", "agreed", "interested_scholarship", ""
]


class BiddingSchema(BaseModel):
    bidding: BiddingEnum
    user_id: Optional[int] = None


StatsEnum = Literal["approved", "refused", "underreview", "waitlist"]


class StatsSchema(BaseModel):
    user_ids: Optional[list[int]] = None
    stats: StatsEnum


class EntrySemesterSchema(BaseModel):
    semester: str


class SectionsDocument(BaseModel):
    list_of_advisors: bool = False
    relation: bool = False
    approved: bool = False
    refused: bool = False
    underreview: bool = False
    general_statistics: bool = False
    show_emails: bool = False
