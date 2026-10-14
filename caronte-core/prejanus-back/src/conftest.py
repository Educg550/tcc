from datetime import date, datetime
from typing import Annotated
from fastapi.params import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from src.auth.exceptions import UserNotAuthenticatedInSenhaunica
from src.infra.database.models.base import Base
from src.infra.database.models.edict import Edict
from src.infra.database.models.submission import Submission
from src.infra.database.models.user import RolesEnum, User
from src.use_cases.dtos import UserDTO

# Configuration fixtures 
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    monkeypatch.setenv("APP_NAME", "test")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_VERSION", "test")
    monkeypatch.setenv("DB_CONNECTION_STRING", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SMTP_SERVER", "email_server@email.com")
    monkeypatch.setenv("SMTP_PORT", "000")
    monkeypatch.setenv("SMTP_USER", "user@email.com")
    monkeypatch.setenv("SMTP_PASSWORD", "password")
    monkeypatch.setenv("FROM_EMAIL", "user@email.com")

@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("PRAGMA foreign_keys = ON"))
        await conn.execute(text("PRAGMA defer_foreign_keys = ON"))
    yield


@pytest.fixture
async def session(engine: AsyncEngine, create_tables):
    async with engine.connect() as connection, connection.begin_nested() as transaction:
        get_test_session = async_sessionmaker(
            expire_on_commit=False, autocommit=False, autoflush=False, bind=connection
        )
        test_session = get_test_session()
        yield test_session

        await test_session.close()
        await transaction.rollback()
        await connection.close()


@pytest.fixture
async def client(session):
    from src.infra.database.session import get_session
    from src.auth.senhaunica_auth import get_user
    from src.main import app

    async def override_get_session():
        try:
            yield session
        finally:
            await session.close()

    async def override_get_user(token:  Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))],):
        if token is not None and token.credentials == "valid_token_for_user_with_id_1":
            return UserDTO(
                id=1,
                name="Test User", 
                email="testuser@example.com",
                nusp="123123"
            )
        raise UserNotAuthenticatedInSenhaunica


    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_user] = override_get_user
    client = TestClient(app)
    yield client

# Application fixtures - these fixtures will be used in more than one/two localized tests

@pytest.fixture
async def an_edict(session):
    edict = Edict(
        title="Um edital de mestrado",
        initial_date=date.fromisoformat("2024-01-10"),
        end_date=date.fromisoformat("2024-03-10"), 
        year=2024, 
        semester=1,
        type="Mestrado",
        is_open=True
    )
    session.add(edict)
    await session.commit()

    return edict


@pytest.fixture
async def another_edict(session):
    edict = Edict(
        title="Um edital passado de doutorado",
        initial_date=date.fromisoformat("2023-06-20"),
        end_date=date.fromisoformat("2023-12-20"), 
        year=2023, 
        semester=2,
        type="Doutorado",
        is_open=False,
    )
    session.add(edict)
    await session.commit()

    return edict

@pytest.fixture
async def edict_b(session):
    edict = Edict(
        title="Terceiro edital de mestrado",
        description="Edital de mestrado da computação, primeiro semestre de 2024",
        initial_date=date.fromisoformat("2024-01-10"),
        end_date=date.fromisoformat("2024-03-10"), 
        created_at=datetime.fromisoformat("2024-01-10"),
        year=2022, 
        semester=2,
        type="Mestrado",
        is_open=False,
        updated_at=datetime.fromisoformat("2024-03-10")
    )
    session.add(edict)
    await session.commit()

    return edict

@pytest.fixture
async def submission_a(session, an_edict):
    submission = Submission(
        edict_id = an_edict.id,
        poscomp_year = 2022,
        poscomp_score = 40,
        special_courses = "Cálculo 1",
        current_occupation = "Analista de sistemas",
        primary_field = "Engenharia de software",
        secondary_field = "Ciência de dados",
        dedication_level = "Integral",
        scholarship_interest = True,
        additional_info = "Mais info",
        first_heard = "Faculdade",
        advisor = "Zé",
        lattes_curriculum = "http://lattes.com",
    )
    session.add(submission)
    await session.commit()

    return submission

@pytest.fixture
async def submission_b(session, another_edict):
    submission = Submission(
        edict_id = another_edict.id,
        poscomp_year = 2022,
        poscomp_score = 15,
        special_courses = "Deep Learning",
        current_occupation = "",
        primary_field = "IA",
        secondary_field = "Computação musical",
        dedication_level = "Parcial",
        scholarship_interest = False,
        additional_info = "Mais info sobre mim",
        first_heard ="Instagram",
        advisor = "Jão",
    )
    session.add(submission)
    await session.commit()

    return submission


@pytest.fixture
async def user_a(session):
    new_user = User(
        name="Test User", 
        email="testuser@example.com",
        nusp="12345678",  # Número USP fictício
        research_field="Engenharia de Software",
        role=RolesEnum.STUDENT,
        created_at=date(2024, 5, 5)
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user

@pytest.fixture
async def user_b(session):
    new_user = User(
        name="Another Test User", 
        email="testuser2@example.com",
        nusp="23456789",  # Número USP fictício
        research_field="Engenharia de Software",
        role=RolesEnum.STUDENT,
        created_at=date(2024, 5, 5)
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user