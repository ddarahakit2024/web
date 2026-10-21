import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-only-change-me-use-env-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", "")
KAKAO_REDIRECT_URI = os.getenv(
    "KAKAO_REDIRECT_URI", "http://localhost:5173/login/kakao/callback"
)
PORTONE_STORE_ID = os.getenv("PORTONE_STORE_ID", "")
PORTONE_CHANNEL_KEY = os.getenv("PORTONE_CHANNEL_KEY", "")
PORTONE_API_SECRET = os.getenv("PORTONE_API_SECRET", "")
