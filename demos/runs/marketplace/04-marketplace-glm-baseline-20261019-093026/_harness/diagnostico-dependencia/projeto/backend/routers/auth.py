from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from backend.deps import get_current_user, get_db, new_session_token
from backend.models import Session as SessionModel, User
from backend.schemas import LoginIn, RegisterIn, UserPatch
from backend.serializers import user_public

router = APIRouter(prefix="/api/auth", tags=["auth"])
hasher = PasswordHasher()


@router.post("/register", status_code=201)
def register(data: RegisterIn, db: OrmSession = Depends(get_db)):
    email = data.email.lower()
    exists = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    user = User(
        name=data.name.strip(),
        email=email,
        password_hash=hasher.hash(data.password),
    )
    db.add(user)
    db.commit()
    return user_public(user)


@router.post("/login")
def login(data: LoginIn, response: Response, db: OrmSession = Depends(get_db)):
    user = db.execute(
        select(User).where(User.email == data.email.lower())
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    try:
        hasher.verify(user.password_hash, data.password)
    except VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = new_session_token()
    db.add(SessionModel(token=token, user_id=user.id))
    db.commit()
    response.set_cookie(
        "session", token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30
    )
    return {"user": user_public(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_public(user)


@router.patch("/me")
def patch_me(
    data: UserPatch,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    user.name = data.name.strip()
    db.commit()
    return user_public(user)


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    db.query(SessionModel).filter(SessionModel.user_id == user.id).delete()
    db.commit()
    response.delete_cookie("session")
