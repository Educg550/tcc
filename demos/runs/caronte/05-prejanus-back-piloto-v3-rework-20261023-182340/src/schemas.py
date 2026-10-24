from datetime import date, datetime
from enum import Enum

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
    year: int
    semester: int
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


class LabelSchema(BaseModel):
    label: str
    color: str


class PrivateNoteSchema(BaseModel):
    note: str


class RequestReesendSchema(BaseModel):
    text: str


class StatsEnum(str, Enum):
    approved = 'approved'
    refused = 'refused'
    underreview = 'underreview'
    waitlist = 'waitlist'


class StatsSchema(BaseModel):
    user_ids: list[int] | None
    stats: StatsEnum


class BiddingEnum(str, Enum):
    decline = 'decline'
    available = 'available'
    interested = 'interested'
    agreed = 'agreed'
    interested_scholarship = 'interested_scholarship'
    none = ''


class BiddingSchema(BaseModel):
    bidding: BiddingEnum
    user_id: int | None = None


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
