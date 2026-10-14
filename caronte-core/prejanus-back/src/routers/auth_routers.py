from fastapi import APIRouter, HTTPException, Request
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from senhaunicapy.identity import Identity
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database.session import get_session

from src.auth.senhaunica_auth import get_user, load_whitelist
from src.use_cases.auth.get_or_register_user import SenhaunicaUserSchema, UserDTO, get_or_register_user

router = APIRouter(prefix="/auth", tags=['auth'])

@router.get(
    '/login',
    description="Get existent user or register if it not exists",
)
async def login(user: UserDTO = Depends(get_user)):
    return user

@router.post(
    '/login/senhaunica',
    description="Get existent user or register if it not exists",
)
async def login_senhaunica(
    request: Request,
    session: AsyncSession = Depends(get_session)):
    config = request.app.state.extensions["senhaunicapy"].config
    oauth_token = request.query_params.get('oauth_token')

    if oauth_token is None:
        try:
            response_request_token = Identity.get_request_token(config=config)
        except Exception:
            raise HTTPException(status_code=500) 

        request.session["request_secret"] = response_request_token.secret_token

        return JSONResponse({ "redirect_to": response_request_token.url })
    else:
        request_secret = request.session.get("request_secret")
        if not request_secret:
            raise HTTPException(status_code=401)

        oauth_verifier = request.query_params.get('oauth_verifier')

        try:
            response_access_token = Identity.get_access_token(oauth_token, request_secret, oauth_verifier, config=config)
        except Exception:
            raise HTTPException(status_code=500) 
        request.session.pop("request_secret", None)

        nusp_whitelist = load_whitelist()
        def filter_fn(vinculos, nusp):
            return nusp in nusp_whitelist

        info = Identity.get_protected_resources(
            response_access_token.access_token,
            response_access_token.access_secret,
            "wsusuario/oauth/usuariousp",
            "POST",
            affiliation_filter=filter_fn,
            config=config
        )

        user = await get_or_register_user(SenhaunicaUserSchema(
            nusp=info["loginUsuario"],
            email=info["emailPrincipalUsuario"],
            name=info["nomeUsuario"],
        ), session)

        request.session["user_id"] = user.id

        return user