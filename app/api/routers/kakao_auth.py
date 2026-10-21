from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.kakao import KakaoServiceError, KakaoTokenError, fetch_kakao_profile
from app.core.security import create_access_token
from app.core.session import set_access_token_cookie
from app.models import KakaoAccount
from app.schemas.kakao import KakaoLoginRequest
from app.schemas.user import LoginResponse

router = APIRouter(prefix="/user/kakao", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def kakao_login(payload: KakaoLoginRequest, response: Response, db: Session = Depends(get_db)):
    try:
        kakao_user_id, nickname = fetch_kakao_profile(payload.code)
    except KakaoTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="카카오 로그인을 확인할 수 없습니다. 다시 시도해 주세요.",
        ) from None
    except KakaoServiceError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="카카오 로그인 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.",
        ) from None

    account = db.get(KakaoAccount, kakao_user_id)
    if account is None:
        account = KakaoAccount(kakao_user_id=kakao_user_id, nickname=nickname)
        db.add(account)
    else:
        account.nickname = nickname
    db.commit()

    token = create_access_token(f"kakao:{kakao_user_id}")
    set_access_token_cookie(response, token)
    return {
        "code": status.HTTP_200_OK,
        "message": "카카오 로그인에 성공했습니다.",
        "result": {"authenticated": True},
    }
