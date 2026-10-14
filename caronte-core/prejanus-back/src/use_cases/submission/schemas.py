from datetime import date, datetime

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel


class LabelSchema(BaseModel):
    id: int
    label: str
    color: str


class GraduationSchema(BaseModel):
    country: str
    course: str
    institution: str
    year: int


class GraduationSummarySchema(GraduationSchema):
    year: int


class PosCompSchema(BaseModel):
    year: int
    score: str


class ResearchFieldsSchema(BaseModel):
    primary: str
    secondary: str


class ResearchSchema(BaseModel):
    program: str
    semester: str
    field: ResearchFieldsSchema
    will_apply_scholarship: bool
    dedication_level: str


class UserSchema(BaseModel):
    id: int
    name: str
    email: Optional[str]


class CommentSchema(BaseModel):
    user: UserSchema
    id: int
    comment: str
    created_at: datetime
    type: str


class SubmissionSummarySchema(BaseModel):
    id: int
    name: str
    email: str
    phone_number: str
    lattes_curriculum: str
    nationality: str
    personal_website: str
    gender: str
    birth_date: date | str
    graduation: GraduationSchema
    poscomp: PosCompSchema | None
    current_occupation: str | None
    research: ResearchSchema
    is_favorite: bool
    disabilities: bool
    ethnicity_race: bool


class BiddingEnum(Enum):
    DECLINE = "decline"
    AVAILABLE = "available"
    INTERESTED = "interested"
    AGREED = "agreed"
    INTERESTED_SCHOLARSHIP = "interested_scholarship"
    NONE = ""


class SentStatus(Enum):
    NOT_SENT = "not_sent"
    SENT = "sent"
    REPLIED = "replied"


class AcceptSchema(BaseModel):
    sent: SentStatus = SentStatus.NOT_SENT
    accept: Optional[str] = None
    comments: Optional[str] = None
    submitted_at: Optional[datetime] = None


class BiddingUserSchema(UserSchema):
    slots: Optional[str] = None


class BiddingUsersSchema(BaseModel):
    data: Dict[str, List[BiddingUserSchema]]


class SubmissionApprovalSchema(BaseModel):
    id: int
    token: str
    name: str
    email: str
    phone_number: str
    nationality: str
    personal_website: str
    gender: str
    advisor: Optional[UserSchema]
    birth_date: date
    graduation: GraduationSchema
    poscomp: PosCompSchema | None
    current_occupation: str | None
    research: ResearchSchema
    lattes_curriculum: str
    stats: str
    is_favorite: bool
    bidding_users: BiddingUsersSchema
    labels: list[LabelSchema]
    disabilities: bool
    ethnicity_race: bool
    accept: AcceptSchema


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
    email: str
    sent: bool


class SubmissionSchema(SubmissionSummarySchema):
    graduation: GraduationSummarySchema
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
