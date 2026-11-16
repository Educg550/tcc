import datetime as dt

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
    date_application: dt.datetime
    date_verification: dt.datetime
    date_evaluation: dt.datetime
    date_closed: dt.datetime


class EditEdictSchema(BaseModel):
    title: str
    description: str
    year: str
    semester: str
    edict_type: str
    date_application: dt.datetime
    date_verification: dt.datetime
    date_evaluation: dt.datetime
    date_closed: dt.datetime


class EditEdictDateSchema(BaseModel):
    closed_date: dt.date


class AdvancePhaseEdictSchema(BaseModel):
    id: int


class CloseEdictSchema(BaseModel):
    confirmation_deadline: dt.date
    send_approval_letter: bool


class SlotsSchema(BaseModel):
    amount: str


class CommentSchema(BaseModel):
    comment: str
    created_at: dt.datetime | None = None
    updated_at: dt.datetime | None = None


class LabelInputSchema(BaseModel):
    label: str
    color: str


class PrivateNoteSchema(BaseModel):
    note: str


class RequestReesendSchema(BaseModel):
    text: str


class StatsSchema(BaseModel):
    user_ids: list[int] | None
    stats: str


class BiddingSchema(BaseModel):
    bidding: str
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
