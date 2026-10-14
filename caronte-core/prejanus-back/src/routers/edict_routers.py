from http import HTTPStatus
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    BackgroundTasks,
)
from typing import Any, Dict, Union
from pydantic import BaseModel, RootModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import exists, select
from typing import List
from src.infra.database.models.edict_form_mapping import EdictFormMapping
from src.infra.database.models.submission import Submission
from src.infra.database.session import get_session, get_session_forms
from src.use_cases.data.interactors_list import SectionsDocument, get_interactors_list
from src.use_cases.data.pairing_biddings import get_pairing_biddings
from src.use_cases.edict.advance_phase import (
    AdvancePhaseEdictResponse,
    AdvancePhaseEdictSchema,
    advance_phase_edict_by_id,
)
from src.use_cases.edict.edit_edict import (
    EditEdictDateResponse,
    EditEdictDateSchema,
    EditEdictResponse,
    EditEdictSchema,
    edit_date_edict_by_id,
    edit_edict_by_id,
)
from src.use_cases.edict.get_all import EdictSchema, get_all_edicts
from src.use_cases.edict.insert_edict import (
    InsertEdictSchema,
    InsertEdictResponse,
    insert_edict,
)
from src.use_cases.edict.remove_edict import remove_edict_by_id
from src.use_cases.edict.set_slots import SlotsResponseSchema, SlotsSchema, set_slots
from src.use_cases.mapping.delete_mapping import delete_mapping
from src.use_cases.submission.get_all_from_edict import (
    GetAllSubmissionsFromEdictResponse,
    query_get_all_submissions_from_edict,
)
from src.use_cases.edict.get_by_id import EdictByIdSchema, get_edict_by_id

# from src.use_cases.edict.send_approved_emails import send_emails_to_approved_submissions
from src.use_cases.edict.close_edict import CloseEdictSchema, close_edict_by_id
from src.auth.senhaunica_auth import get_user
from src.use_cases.auth.get_or_register_user import UserDTO
from src.use_cases.mapping.update_mapping import update_mapping
from src.use_cases.mapping.create_mapping import create_mapping
from src.utils import is_admin_role
from src.utils.download_file import (
    download_generate_csv_file,
    download_generate_pdf_file,
)

router = APIRouter(prefix="/edicts", tags=["edicts"])


@router.get(
    "",
    description="Get all edicts from the application (respecting the selected filters, if filled).",
    response_model=List[EdictSchema],
)
async def get_all(
    auth_user: UserDTO = Depends(get_user),  # force auth route
    session: AsyncSession = Depends(get_session),
    type: str | None = Query(None, description="Filter by type of edict."),
    is_open: bool | None = Query(None, description="Filter by open/closed edicts."),
):
    edicts = await get_all_edicts(session, type=type, is_open=is_open)
    return edicts


@router.get(
    "/{edict_id}/submissions",
    description="Get all submissions from the application associated with a given edict.",
    response_model=GetAllSubmissionsFromEdictResponse,
)
async def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool | None = Query(
        False,
        description="Filter to only show favorite submissions of a specific user.",
    ),
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms),
):
    user_id = None
    if only_favorites:
        user_id = auth_user.id
    submissions = await query_get_all_submissions_from_edict(
        session, session_forms, edict_id, auth_user.id, user_id, stats
    )
    return {"submissions": submissions}


@router.post("", description="Create a new edict.", response_model=InsertEdictResponse)
async def create_edict(
    edict_data: InsertEdictSchema,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
):
    new_edict = await insert_edict(session, edict_data, auth_user)
    return new_edict


@router.get(
    "/{edict_id}", description="Get edict by its ID", response_model=EdictByIdSchema
)
async def get_edict(
    edict_id: int,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
):
    edict_details = await get_edict_by_id(session, edict_id, auth_user)
    return edict_details


@router.post(
    "/{edict_id}/edit",
    description="Edit edict by its ID",
    response_model=EditEdictResponse,
)
async def edit_date_edict(
    edict_id: int,
    edict_data: EditEdictSchema,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
):
    edit_details = await edit_edict_by_id(session, edict_id, edict_data, auth_user)
    return edit_details


@router.post(
    "/{edict_id}/edit-date",
    description="Edit date edict by its ID",
    response_model=EditEdictDateResponse,
)
async def edit_edict_date_only(
    edict_id: int,
    edict_date_data: EditEdictDateSchema,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
):
    edit_details = await edit_date_edict_by_id(
        session, edict_id, edict_date_data, auth_user
    )
    return edit_details


@router.post(
    "/{edict_id}/advance-phase",
    description="Advance phase edict by its ID",
    response_model=AdvancePhaseEdictResponse,
)
async def advance_edict(
    edict_id: int,
    edict_phase_data: AdvancePhaseEdictSchema,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms),
):
    edit_details = await advance_phase_edict_by_id(
        session, session_forms, edict_id, edict_phase_data, auth_user
    )
    return edit_details


@router.delete(
    "/{edict_id}/remove",
    description="Remove a given edict.",
)
async def remove_edict(
    edict_id: int,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
):
    await remove_edict_by_id(session, edict_id, auth_user)

    return Response(status_code=HTTPStatus.OK)


@router.post("/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: int,
    background_tasks: BackgroundTasks,
    section_document: SectionsDocument = {},
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms),
    mode: str = "plain_text",
):
    return await get_interactors_list(
        edict_id=edict_id,
        section_document=section_document,
        auth_user=auth_user,
        session=session,
        session_forms=session_forms,
        background_tasks=background_tasks,
        mode=mode,
    )


@router.post("/{edict_id}/pairing-biddings")
async def pairing_biddings(
    edict_id: int,
    background_tasks: BackgroundTasks,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms),
):
    return await get_pairing_biddings(
        edict_id=edict_id,
        auth_user=auth_user,
        session=session,
        session_forms=session_forms,
        background_tasks=background_tasks,
    )


@router.get("/download_pdf/{job_id}")
async def download_pdf(job_id: str):
    return await download_generate_pdf_file(job_id)


@router.get("/download_csv/{job_id}")
async def download_csv(job_id: str):
    return await download_generate_csv_file(job_id)


@router.post(
    "/{edict_id}/slots",
    description="Definir quantidade de vagas por orientador do edital",
    response_model=SlotsResponseSchema,
)
async def set_user_slots(
    edict_id: int,
    slots_data: SlotsSchema,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
):
    return await set_slots(edict_id, session, slots_data, auth_user)


@router.patch(
    "/{edict_id}/close",
    description="Closes a given edict.",
)
async def close_edict(
    edict_id: int,
    close_edict_data: CloseEdictSchema,
    background_tasks: BackgroundTasks,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
):
    await close_edict_by_id(session, edict_id, auth_user)

    # TODO: realizar envio de cartas de aprovação
    # if close_edict_data.send_approval_letter == True:
    #     response = await send_emails_to_approved_submissions(
    #         session=session,
    #         edict_id=edict_id,
    #         confirmation_deadline=close_edict_data.confirmation_deadline,
    #         background_tasks=background_tasks
    #     )

    #     return response

    return Response(status_code=HTTPStatus.OK)


class EdictFormMappingResponse(BaseModel):
    id: int
    edict_id: int
    form_id: str
    form_type: str
    form_version: str
    mapping: Any
    is_active: bool

    class Config:
        from_attributes = True


class MappingLeaf(BaseModel):
    section: int
    field: int


class MappingNode(RootModel):
    root: Dict[str, Union["MappingNode", MappingLeaf, None]]


PostMappingSchema = MappingNode


@router.post("/{edict_id}/recommenders/mappings/versions/{version}/")
async def create_recommender_form_mapping(
    edict_id: int,
    mapping: PostMappingSchema,
    version: int = 1,
    auth_user: UserDTO = Depends(get_user),  # force auth route
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms),
):
    return await create_mapping(
        edict_id,
        mapping,
        "recommender",
        version,
        auth_user,
        session,
        session_forms,
    )


@router.post("/{edict_id}/candidates/mappings/versions/{version}/")
async def create_candidate_form_mapping(
    edict_id: int,
    mapping: PostMappingSchema,
    version: int = 1,
    auth_user: UserDTO = Depends(get_user),  # force auth route
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms),
):
    return await create_mapping(
        edict_id,
        mapping,
        "candidate",
        version,
        auth_user,
        session,
        session_forms,
    )


@router.get("/{edict_id}/candidates/mappings")
async def get_submission_form_mapping(
    edict_id: int,
    auth_user: UserDTO = Depends(get_user),  # force auth route
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms),
):

    edict_form_mappings = (
        (
            await session.execute(
                select(EdictFormMapping).where(
                    EdictFormMapping.edict_id == edict_id,
                    EdictFormMapping.form_type == "candidate",
                )
            )
        )
        .scalars()
        .all()
    )

    return edict_form_mappings


@router.get("/{edict_id}/recommenders/mappings")
async def get_recommender_form_mapping(
    edict_id: int,
    auth_user: UserDTO = Depends(get_user),  # force auth route
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms),
):

    edict_form_mappings = (
        (
            await session.execute(
                select(EdictFormMapping).where(
                    EdictFormMapping.edict_id == edict_id,
                    EdictFormMapping.form_type == "recommender",
                )
            )
        )
        .scalars()
        .all()
    )

    return edict_form_mappings


@router.put("/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
async def update_recommender_mapping(
    edict_id: int,
    mapping_id: int,
    payload: dict,
    version: int,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms),
):
    # Se não é administrador
    if not is_admin_role(auth_user.role):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
        )

    return await update_mapping(
        form_type="recommender",
        mapping_id=mapping_id,
        edict_id=edict_id,
        version=version,
        new_mapping=payload,
        auth_user=auth_user,
        session=session,
    )


@router.put("/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
async def update_candidate_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    payload: dict,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
    session_forms: AsyncSession = Depends(get_session_forms),
):
    # Se não é administrador
    if not is_admin_role(auth_user.role):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
        )

    return await update_mapping(
        form_type="candidate",
        mapping_id=mapping_id,
        edict_id=edict_id,
        version=version,
        new_mapping=payload,
        auth_user=auth_user,
        session=session,
    )


@router.delete("/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
async def delete_candidate_mapping(
    edict_id: int,
    mapping_id: int,
    version: int,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
):
    # Se não é administrador
    if not is_admin_role(auth_user.role):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
        )

    return await delete_mapping(
        form_type="candidate",
        mapping_id=mapping_id,
        edict_id=edict_id,
        version=version,
        auth_user=auth_user,
        session=session,
    )


@router.delete("/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
async def delete_recommender_mapping(
    edict_id: int,
    mapping_id: int,
    version: int,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
):
    # Se não é administrador
    if not is_admin_role(auth_user.role):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
        )

    return await delete_mapping(
        form_type="recommender",
        mapping_id=mapping_id,
        version=version,
        edict_id=edict_id,
        auth_user=auth_user,
        session=session,
    )


@router.get("/{edict_id}/candidates/forms/versions/unmapped")
async def get_candidates_unmapped_versions(
    edict_id: int,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
):
    mapped_version = select(EdictFormMapping.id).where(
        EdictFormMapping.edict_id == edict_id,
        EdictFormMapping.form_type == "candidate",
        EdictFormMapping.form_version == Submission.candidate_form_version,
    )
    versions = (
        (
            await session.execute(
                select(Submission.candidate_form_version)
                .where(
                    Submission.edict_id == edict_id,
                    ~exists(mapped_version),
                )
                .distinct()
            )
        )
        .scalars()
        .all()
    )

    return versions


@router.get("/{edict_id}/recommenders/forms/versions/unmapped")
async def get_recommenders_unmapped_versions(
    edict_id: int,
    auth_user: UserDTO = Depends(get_user),
    session: AsyncSession = Depends(get_session),
):
    mapped_version = select(EdictFormMapping.id).where(
        EdictFormMapping.edict_id == edict_id,
        EdictFormMapping.form_type == "recommender",
        EdictFormMapping.form_version == Submission.recommender_form_version,
    )
    versions = (
        (
            await session.execute(
                select(Submission.recommender_form_version)
                .where(
                    Submission.edict_id == edict_id,
                    ~exists(mapped_version),
                )
                .distinct()
            )
        )
        .scalars()
        .all()
    )

    return versions
