from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routers import auth, courses, kakao_auth, payments, users
from app.db.database import Base, SessionLocal, get_db
from app.models import User  # noqa: F401 - register model metadata


def create_app(session_factory=SessionLocal, create_schema: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_application):
        if create_schema:
            Base.metadata.create_all(bind=session_factory.kw["bind"])
        yield

    application = FastAPI(title="회원 인증 API", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://www.mlops.kro.kr",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(_request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "message": str(exc.detail), "result": None},
            headers=exc.headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, _exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"code": 422, "message": "요청 값이 올바르지 않습니다.", "result": None},
        )

    @application.exception_handler(Exception)
    async def internal_error_handler(_request: Request, _exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "서버 내부 오류가 발생했습니다.", "result": None},
        )

    application.include_router(users.router)
    application.include_router(auth.router)
    application.include_router(kakao_auth.router)
    application.include_router(courses.router)
    application.include_router(payments.router)
    if session_factory is not SessionLocal:
        application.dependency_overrides[get_db] = _session_dependency(session_factory)
    return application


def _session_dependency(session_factory):
    def dependency():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()
    return dependency


app = create_app()
