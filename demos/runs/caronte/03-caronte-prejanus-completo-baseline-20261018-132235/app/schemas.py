"""Pydantic schemas, named after the original OpenAPI components."""
from datetime import date, datetime

from pydantic import BaseModel, Field


class EdictSchema(BaseModel):
    id: int
    title: str
    year: int
    semester: int
    edict_type: str
    is_open: bool


class EdictPhaseResponse(BaseModel):
    id: int
    closed_date: date | None = None
    phase: str


class EdictByIdSchema(BaseModel):
    id: int
    title: str
    candidate_form_id: str
    recommender_form_id: str
    description: str = ""
    closed_date: date | None = None
    created_at: datetime | None = None
    year: int
    semester: int
    type: str
    is_open: bool
    updated_at: datetime | None = None
    phase: str
    phases: list[EdictPhaseResponse]
    slots: str


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


class InsertEdictResponse(BaseModel):
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
    id: int
    closed_date: datetime


class EditEdictSchema(BaseModel):
    title: str
    description: str
    year: str
    semester: str
    edict_type: str
    date_application: datetime
    date_verification: datetime
    date_evaluation: datetime
    date_closed: datetime


class EditEdictResponse(BaseModel):
    title: str
    description: str
    year: str
    semester: str
    edict_type: str
    date_application: datetime
    date_verification: datetime
    date_evaluation: datetime
    date_closed: datetime


class EditEdictDateSchema(BaseModel):
    closed_date: date


class EditEdictDateResponse(BaseModel):
    closed_date: date


class AdvancePhaseEdictSchema(BaseModel):
    id: int


class AdvancePhaseEdictResponse(BaseModel):
    id: int
    label: str


class CloseEdictSchema(BaseModel):
    confirmation_deadline: date
    send_approval_letter: bool


class SlotsSchema(BaseModel):
    amount: str


class SlotsResponseSchema(BaseModel):
    amount: str


class MappingLeaf(BaseModel):
    section: int
    field: int


class MappingNode(BaseModel):
    """A mapping tree node: nested groups, leaves and null placeholders."""

    model_config = {"extra": "allow"}


class UserResponseSchema(BaseModel):
    id: int
    name: str


class UserSchema(BaseModel):
    id: int
    name: str
    email: str | None = None


class GraduationSchema(BaseModel):
    country: str = ""
    course: str = ""
    institution: str = ""
    year: int = 0


class PosCompSchema(BaseModel):
    year: int = 0
    score: str = ""


class ResearchFieldsSchema(BaseModel):
    primary: str = ""
    secondary: str = ""


class ResearchSchema(BaseModel):
    program: str = ""
    semester: str = ""
    field: ResearchFieldsSchema = ResearchFieldsSchema()
    will_apply_scholarship: bool = False
    dedication_level: str = ""


class AcceptSchema(BaseModel):
    sent: str = "not_sent"
    accept: str | None = None
    comments: str | None = None
    submitted_at: datetime | None = None


class BiddingUserSchema(BaseModel):
    id: int
    name: str
    email: str | None = None
    slots: str | None = None


class BiddingUsersSchema(BaseModel):
    data: dict[str, list[BiddingUserSchema]] = Field(default_factory=dict)


class LabelSchemaOutput(BaseModel):
    id: int
    label: str
    color: str


class LabelSchemaInput(BaseModel):
    label: str
    color: str


class LabelResponseSchema(BaseModel):
    id: int
    user: UserResponseSchema
    submission_id: int
    label: str


class UserLabelResponseSchema(BaseModel):
    labels: list[LabelSchemaOutput]


class SubmissionSchema(BaseModel):
    id: int
    token: str
    name: str
    email: str
    phone_number: str = ""
    nationality: str = ""
    personal_website: str = ""
    gender: str = ""
    advisor: UserSchema | None = None
    birth_date: date | None = None
    graduation: GraduationSchema = GraduationSchema()
    poscomp: PosCompSchema | None = None
    current_occupation: str | None = None
    research: ResearchSchema = ResearchSchema()
    lattes_curriculum: str = ""
    stats: str = "underreview"
    is_favorite: bool = False
    bidding_users: BiddingUsersSchema = BiddingUsersSchema()
    labels: list[LabelSchemaOutput] = []
    disabilities: bool = False
    ethnicity_race: bool = False
    accept: AcceptSchema = AcceptSchema()


class GetAllSubmissionsFromEdictResponse(BaseModel):
    submissions: list[SubmissionSchema]


class CommentSchema(BaseModel):
    comment: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CommentResponseSchema(BaseModel):
    id: int
    user: UserResponseSchema
    submission_id: int
    comment: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PrivateNoteSchema(BaseModel):
    note: str


class RequestReesendSchema(BaseModel):
    text: str


class RequestReesendResponse(BaseModel):
    message: str
    email_sent: str


class StatsSchema(BaseModel):
    user_ids: list[int] | None = None
    stats: str


class BiddingSchema(BaseModel):
    bidding: str
    user_id: int | None = None


class EntrySemesterSchema(BaseModel):
    semester: str


class SendAcceptFormsByIdResponse(BaseModel):
    message: str
    email_sent: str


class SendAcceptLettersByIdResponse(BaseModel):
    message: str
    email_sent: str


class SectionsDocument(BaseModel):
    list_of_advisors: bool | None = False
    relation: bool | None = False
    approved: bool | None = False
    refused: bool | None = False
    underreview: bool | None = False
    general_statistics: bool | None = False
    show_emails: bool | None = False


class LoginSchema(BaseModel):
    id: int
    name: str
    email: str | None = None
    nusp: str | None = None
    role: str


class MappingResponseSchema(BaseModel):
    id: int
    edict_id: int
    form_type: str
    user: UserResponseSchema | None = None
    version: int
    tree: dict
    active: bool