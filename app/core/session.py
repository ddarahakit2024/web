from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
import jwt

from app.api.deps import get_db
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET_KEY
from app.models import KakaoAccount, User

ACCESS_TOKEN_COOKIE = "access_token"


def set_access_token_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=True,
        samesite="none",
        partitioned=True,
        path="/",
    )


def get_current_subject(request: Request, db: Session = Depends(get_db)) -> str:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        raise _unauthorized()
    try:
        claims = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise _unauthorized() from None

    subject = claims.get("sub")
    if not isinstance(subject, str):
        raise _unauthorized()
    if subject.startswith("kakao:"):
        account = db.get(KakaoAccount, subject.removeprefix("kakao:"))
        if account is None:
            raise _unauthorized()
        return subject

    try:
        user_id = int(subject)
    except ValueError:
        raise _unauthorized() from None
    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized()
    return subject


def get_current_profile(request: Request, db: Session) -> dict[str, str]:
    subject = get_current_subject(request, db)
    if subject.startswith("kakao:"):
        account = db.get(KakaoAccount, subject.removeprefix("kakao:"))
        return {"name": account.nickname, "provider": "kakao"}
    user = db.get(User, int(subject))
    return {"name": user.name, "provider": "local"}


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
    )
