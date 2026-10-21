from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import hash_password
from app.models import User
from app.schemas.user import SignupRequest, SignupResponse

router = APIRouter(prefix="/user", tags=["users"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="이미 사용 중인 이메일입니다.")
    user = User(email=payload.email, hashed_password=hash_password(payload.password), name=payload.name)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="이미 사용 중인 이메일입니다.") from None
    db.refresh(user)
    return {"code": status.HTTP_201_CREATED, "message": "회원가입이 완료되었습니다.", "result": user}
