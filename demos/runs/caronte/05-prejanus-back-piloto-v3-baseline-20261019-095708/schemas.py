from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel


class InsertEdictSchema(BaseModel):
    title: str
    description: str | None = None
    year: int
    semester: int
    edict_type: str
    is_open: bool
    candidate_forms: int
    recommenders_forms: int
    date_application: datetime
    date_verification: datetime
    date_evaluation: datetime
    date_closed: datetime


class EditEdictSchema(BaseModel):
    title: str
    description: str | None = None
    year: str
    semester: str
    edict_type: str
    date_application: datetime
    date_verification: datetime
    date_evaluation: datetime
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
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LabelInputSchema(BaseModel):
    label: str
    color: str


class PrivateNoteSchema(BaseModel):
    note: str


class RequestReesendSchema(BaseModel):
    text: str


class StatsSchema(BaseModel):
    user_ids: list[int] | None
    stats: Literal["approved", "refused", "underreview", "waitlist"]


BIDDING_VALUES = ("decline", "available", "interested", "agreed", "interested_scholarship", "")


class BiddingSchema(BaseModel):
    bidding: Literal[
        "decline",
        "available",
        "interested",
        "agreed",
        "interested_scholarship",
        "",
    ]
    user_id: int | None = None


class EntrySemesterSchema(BaseModel):
    semester: str


class SectionsDocument(BaseModel):
    list_of_advisors: bool | None = False
    relation: bool | None = False
    approved: bool | None = False
    refused: bool | None = False
    underreview: bool | None = False
    general_statistics: bool | None = False
    show_emails: bool | None = False


MappingTree = dict[str, Any]
