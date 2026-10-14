from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Query, Response, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse

from src.auth.senhaunica_auth import get_user
from src.infra.database.session import get_session, get_session_forms
from src.use_cases.auth.get_or_register_user import UserDTO
from src.use_cases.submission.change_bidding import BiddingSchema, change_bidding_by_submission
from src.use_cases.submission.change_semester import EntrySemesterSchema, change_semester_by_submission
from src.use_cases.submission.delete_label import delete_label
from src.use_cases.submission.get_by_id import get_submission_by_id,load_activity

#Comment
from src.use_cases.submission.get_file import get_file_by_submission
from src.use_cases.submission.get_label import UserLabelResponseSchema, get_label_by_userid
from src.use_cases.submission.insert_comment import CommentSchema, CommentResponseSchema, insert_comment
from src.use_cases.submission.delete_comment import delete_comment

#Favorites
from src.use_cases.submission.insert_favorite import insert_favorite
from src.use_cases.submission.delete_favorite import delete_favorite
from src.use_cases.submission.exceptions import FavoriteNotFound

from src.use_cases.submission.insert_label import LabelResponseSchema, LabelSchema, insert_label
from src.use_cases.submission.private_notes.insert_or_update_notes import PrivateNoteSchema, insert_or_update_notes
from src.use_cases.submission.request_reesend import RequestReesendResponse, RequestReesendSchema, request_reesend

from src.use_cases.submission.select_stats_submission import StatsSchema, select_stats_submission
from src.use_cases.submission.send_accept_forms import SendAcceptFormsByIdResponse, send_accept_forms_by_id
from src.use_cases.submission.send_accept_letter import SendAcceptLettersByIdResponse, send_accept_letter_by_id

# Views
from src.use_cases.submission.create_submission_view import create_submission_view
from src.use_cases.submission.get_by_id import get_views_by_submission_id
router = APIRouter(prefix='/submissions', tags=['submissions'])

@router.get(
    "/{submission_id}",
    description="Get submission details by its ID.",
    #response_model=GetSubmissionDetailsResponse
)
async def get_details(
    submission_id: int,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms),
    include_comments: bool = Query(False, description="Include the submission comments in the response.")
):
    submission = await get_submission_by_id(submission_id, auth_user, session, session_forms, include_comments=include_comments)
    return submission

@router.post(
    "/{submission_id}/send-accept",
    description="Send accept e-emails.",
    response_model=SendAcceptFormsByIdResponse
)
async def send_accept_forms(
    submission_id: int,
    background_tasks: BackgroundTasks,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms),
):
    sender = await send_accept_forms_by_id(submission_id, session, session_forms, background_tasks)
    return sender

@router.post(
    "/{submission_id}/send-letter",
    description="Send accept letter e-emails.",
    response_model=SendAcceptLettersByIdResponse
)
async def send_accept_letter(
    submission_id: int,
    background_tasks: BackgroundTasks,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms),
):
    sender = await send_accept_letter_by_id(submission_id, session, session_forms, background_tasks)
    return sender

@router.get("/{submission_id}/comments", description= "Get all comments from a specific submission")
async def get_all_comments(submission_id:int,auth_user:UserDTO = Depends(get_user),session:AsyncSession = Depends(get_session),session_forms: AsyncSession = Depends(get_session_forms)):
    comments = (await load_activity(submission_id,session,session_forms,True))
    return comments

@router.post(
    "/{submission_id}/comments",
    description="Add a comment to a specific submission.",
    response_model=CommentResponseSchema,
)
async def add_comment(
    submission_id: int,
    comment_data: CommentSchema,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session)
): 
    new_comment = await insert_comment(submission_id, session, comment_data , auth_user)

    return new_comment

@router.get(
    "/{submission_id}/labels",
    description="Get all labels by user.",
    response_model=UserLabelResponseSchema,
)
async def get_label(
    submission_id: int,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session)
): 
    label = await get_label_by_userid(submission_id, auth_user.id, session)

    return label

@router.post(
    "/{submission_id}/labels",
    description="Add a label to a specific submission.",
    response_model=LabelResponseSchema,
)
async def add_label(
    submission_id: int,
    label_data: LabelSchema,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session)
): 
    new_label = await insert_label(submission_id, session, label_data, auth_user)

    return new_label

@router.delete(
    "/label/{label_id}",
    description="Delete a label from a specific submission.",
)
async def remove_label(
    label_id: int,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session)
):
    await delete_label(session, label_id, auth_user)

    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post(
    "/{submission_id}/private_notes",
    description="Add or update a private note to a specific submission by user.",
    response_model=PrivateNoteSchema,
)
async def add_or_update_note(
    submission_id: int,
    note_data: PrivateNoteSchema,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session)
): 
    note = await insert_or_update_notes(submission_id, session, note_data, auth_user)

    return note

@router.post(
    "/{submission_id}/reesend_submission",
    description="Request resubmission.",
    response_model=RequestReesendResponse,
)
async def reesend_submission(
    submission_id: int,
    data: RequestReesendSchema,
    background_tasks: BackgroundTasks,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms),
): 
    data = await request_reesend(submission_id, session, session_forms, data, auth_user, background_tasks)
    return data

@router.delete(
    "/comments/{comment_id}",
    description="Delete a comment from a specific submission.",
)
async def remove_comment(
    comment_id: int,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session)
):
    await delete_comment(session, comment_id, auth_user)

    return Response(status_code=HTTPStatus.NO_CONTENT)


#Favorites
@router.post("/{submission_id}/favorites")
async def create_favorite(
    submission_id: int, 
    auth_user: UserDTO = Depends(get_user), 
    session: AsyncSession = Depends(get_session)) -> str:
    await insert_favorite(session, auth_user.id, submission_id)

    return Response(status_code=HTTPStatus.CREATED)


@router.delete("/{submission_id}/favorites")
async def remove_favorite(
    submission_id: int, 
    auth_user: UserDTO = Depends(get_user), 
    session: AsyncSession = Depends(get_session)) -> str:
    try:
        await delete_favorite(session, auth_user.id, submission_id)
        return Response(status_code=HTTPStatus.NO_CONTENT)
    except FavoriteNotFound as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e))

@router.post(
    "/{submission_id}/select",
    description="Marks the given submission as stats."
)
async def select_stats(
    submission_id: int,
    stats_data: StatsSchema,
    auth_user: UserDTO = Depends(get_user), 
    session: AsyncSession = Depends(get_session)) -> str:
    await select_stats_submission(submission_id, stats_data.user_ids, stats_data.stats, session, auth_user)
    return Response(status_code=HTTPStatus.OK)

@router.post(
    "/{submission_id}/bidding",
    description="Toggle bidding option in submission."
)
async def toggle_bidding(
    submission_id: int,
    bidding_data: BiddingSchema,
    auth_user: UserDTO = Depends(get_user), 
    session: AsyncSession = Depends(get_session)) -> str:
    await change_bidding_by_submission(auth_user, submission_id, bidding_data, session)
    return Response(status_code=HTTPStatus.OK)

@router.post(
    "/{submission_id}/entry-semester",
    description="Toggle entry semester option in submission."
)
async def toggle_entry_semester(
    submission_id: int,
    entry_semester_data: EntrySemesterSchema,
    auth_user: UserDTO = Depends(get_user), 
    session: AsyncSession = Depends(get_session)) -> str:
    await change_semester_by_submission(submission_id, entry_semester_data.semester, session)
    return Response(status_code=HTTPStatus.OK)

@router.get(
    "/{submission_id}/files/{label}/{filename}",
    description="Get file with submission.",
)
async def get_file(
    submission_id: int,
    label: str,
    filename: str,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms)
): 
    try:
        result = await get_file_by_submission(submission_id, label, filename, session, session_forms, auth_user)
        result.seek(0)
        return StreamingResponse(
            result,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except FavoriteNotFound as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e))

@router.post(
    "/{submission_id}/view",
    description="Register a view for a submission"
)
async def register_view(submission_id:int,auth_user:UserDTO = Depends(get_user),session:AsyncSession = Depends(get_session),session_forms: AsyncSession = Depends(get_session_forms)):
    await create_submission_view(submission_id, session , auth_user)
    return Response(status_code=HTTPStatus.OK)


@router.get(
    "/{submission_id}/view",
    description="Get the view from a submission"
)
async def get_submission_views(submission_id:int,auth_user:UserDTO = Depends(get_user),session:AsyncSession = Depends(get_session),session_forms: AsyncSession = Depends(get_session_forms)):
    views = await get_views_by_submission_id(submission_id,auth_user,session)
    return views
