from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import create_access_token, verify_password
from app.core.session import get_current_profile, set_access_token_cookie
from app.models import User
from app.schemas.user import LoginRequest, LoginResponse

router = APIRouter(prefix="/user", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    token = create_access_token(str(user.id))
    set_access_token_cookie(response, token)
    return {
        "code": status.HTTP_200_OK,
        "message": "로그인에 성공했습니다.",
        "result": {"authenticated": True},
    }


@router.get("/me")
def current_user(request: Request, db: Session = Depends(get_db)):
    return {
        "code": status.HTTP_200_OK,
        "message": "Authenticated user profile.",
        "result": get_current_profile(request, db),
    }
