import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from prejanus.config import settings
from prejanus.routers import auth, edicts, forms, submissions

app = FastAPI(title=settings.app_name, version=settings.app_version)

# Diagnóstico: codifica a classe da exceção em um status 5xx específico.
EXC_CODES = {
    "ProgrammingError": 550,
    "UndefinedTableError": 551,
    "UndefinedFunctionError": 552,
    "SyntaxError": 553,
    "InvalidPasswordError": 554,
    "OperationalError": 555,
    "InterfaceError": 556,
    "InternalError": 557,
    "InvalidTextRepresentationError": 558,
    "InvalidCatalogNameError": 559,
    "UndefinedColumnError": 560,
    "PermissionDeniedError": 561,
    "InsufficientPrivilegeError": 561,
    "InFailedSqlTransactionError": 562,
    "NotNullViolationError": 563,
    "UniqueViolationError": 564,
    "ForeignKeyViolationError": 565,
    "DatatypeMismatchError": 566,
    "DataError": 567,
    "DuplicateObjectError": 568,
    "TypeError": 570,
    "AttributeError": 571,
    "KeyError": 572,
    "ValueError": 573,
    "JSONDecodeError": 574,
    "UnicodeDecodeError": 574,
    "OSError": 575,
    "InvalidRequestError": 576,
    "NoResultFound": 577,
    "MultipleResultsFound": 577,
    "PendingRollbackError": 578,
    "NoSuchTableError": 579,
    "NoReferencedTableError": 579,
    "GreenletError": 580,
    "TimeoutError": 581,
    "UnmappedInstanceError": 583,
    "DisconnectionError": 584,
    "DatabaseError": 585,
    "IntegrityError": 586,
    "DBAPIError": 587,
}


def _exc_code(exc: Exception) -> int:
    candidates = []
    orig = getattr(exc, "orig", None)
    if orig is not None and orig is not exc:
        candidates.append(orig)
    candidates.append(exc)
    for candidate in candidates:
        for cls in type(candidate).__mro__:
            code = EXC_CODES.get(cls.__name__) or EXC_CODES.get(cls.__name__ + "Error")
            if code:
                return code
    return 588


@app.exception_handler(Exception)
async def _debug_exception_handler(request: Request, exc: Exception):
    code = _exc_code(exc)
    tb = "".join(traceback.format_exception(exc))
    try:
        with open("diag.log", "a", encoding="utf-8") as f:
            f.write(f"=== {request.method} {request.url.path} [code {code}]\n{tb}\n")
    except Exception:
        pass
    return PlainTextResponse(str(code), status_code=code)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(auth.router)
app.include_router(forms.router)
app.include_router(edicts.router)
app.include_router(submissions.router)
