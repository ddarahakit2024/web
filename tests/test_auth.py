import json
import urllib.error
import urllib.request
from http.cookies import SimpleCookie

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import kakao
from app.core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.db.database import Base
from app.main import create_app
from app.models import User


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    test_session = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    with TestClient(create_app(test_session, create_schema=False)) as test_client:
        yield test_client, test_session
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_signup_persists_user_with_hashed_password(client):
    test_client, test_session = client
    response = test_client.post(
        "/user/signup",
        json={"email": "  TEST@example.com ", "password": "secure-pass-123", "name": " Alice "},
    )
    assert response.status_code == 201
    assert response.json()["code"] == 201
    assert response.json()["message"]
    assert response.json()["result"]["email"] == "test@example.com"
    assert response.json()["result"]["name"] == "Alice"
    assert "hashed_password" not in response.json()["result"]
    with test_session() as db:
        user = db.query(User).one()
        assert user.hashed_password != "secure-pass-123"
        assert user.hashed_password.startswith("pbkdf2_sha256$")


def test_duplicate_email_is_case_insensitive_conflict(client):
    test_client, _ = client
    body = {"email": "person@example.com", "password": "secure-pass-123", "name": "Person"}
    assert test_client.post("/user/signup", json=body).status_code == 201
    response = test_client.post("/user/signup", json={**body, "email": "PERSON@example.com"})
    assert response.status_code == 409
    assert response.json() == {
        "code": 409,
        "message": "이미 사용 중인 이메일입니다.",
        "result": None,
    }


def test_login_sets_http_only_cookie_without_returning_token(client):
    test_client, _ = client
    test_client.post(
        "/user/signup",
        json={"email": "person@example.com", "password": "secure-pass-123", "name": "Person"},
    )
    response = test_client.post(
        "/user/login", json={"email": "PERSON@example.com", "password": "secure-pass-123"}
    )
    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["message"]
    assert "access_token" not in response.text
    cookie = get_access_token_from_response(response)
    cookie_header = response.headers["set-cookie"].lower()
    assert "httponly" in cookie_header
    assert "samesite=none" in cookie_header
    assert "secure" in cookie_header
    assert "partitioned" in cookie_header
    assert "domain=mlops.kro.kr" in cookie_header
    claims = jwt.decode(cookie, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert claims["sub"] == "1"
    assert "exp" in claims


def test_cors_allows_production_frontend_with_credentials(client):
    test_client, _ = client
    response = test_client.options(
        "/user/login",
        headers={
            "Origin": "https://www.mlops.kro.kr",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://www.mlops.kro.kr"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_current_user_returns_profile_from_http_only_cookie(client):
    test_client, _ = client
    test_client.post(
        "/user/signup",
        json={"email": "person@example.com", "password": "secure-pass-123", "name": "Person"},
    )
    login = test_client.post(
        "/user/login", json={"email": "person@example.com", "password": "secure-pass-123"}
    )
    response = test_client.get(
        "/user/me", headers={"cookie": f"access_token={get_access_token_from_response(login)}"}
    )
    assert response.status_code == 200
    assert response.json()["result"] == {"name": "Person", "provider": "local"}


def test_current_user_rejects_missing_or_invalid_cookie(client):
    test_client, _ = client
    assert test_client.get("/user/me").status_code == 401
    assert test_client.get("/user/me", headers={"cookie": "access_token=invalid"}).status_code == 401


@pytest.mark.parametrize(
    "email,password",
    [("missing@example.com", "secure-pass-123"), ("person@example.com", "wrong-pass-123")],
)
def test_invalid_credentials_return_401(client, email, password):
    test_client, _ = client
    test_client.post(
        "/user/signup",
        json={"email": "person@example.com", "password": "secure-pass-123", "name": "Person"},
    )
    response = test_client.post("/user/login", json={"email": email, "password": password})
    assert response.status_code == 401
    assert set(response.json()) == {"code", "message", "result"}
    assert response.json()["code"] == 401
    assert response.json()["message"]
    assert response.json()["result"] is None


def test_signup_rejects_short_password(client):
    test_client, _ = client
    response = test_client.post(
        "/user/signup", json={"email": "person@example.com", "password": "short", "name": "Person"}
    )
    assert response.status_code == 422
    assert response.json() == {
        "code": 422,
        "message": "요청 값이 올바르지 않습니다.",
        "result": None,
    }


def test_not_found_uses_standard_response_envelope(client):
    test_client, _ = client
    response = test_client.get("/missing")
    assert response.status_code == 404
    assert set(response.json()) == {"code", "message", "result"}
    assert response.json()["code"] == 404
    assert response.json()["result"] is None


def test_kakao_login_sets_http_only_cookie_without_returning_token(client, monkeypatch):
    test_client, _ = client
    install_kakao_api(monkeypatch, [{"id": 123456789, "kakao_account": {"profile": {"nickname": "Moa"}}}])
    response = test_client.post("/user/kakao/login", json={"code": "authorization-code"})
    assert response.status_code == 200
    assert "access_token" not in response.text
    cookie = get_access_token_from_response(response)
    claims = jwt.decode(cookie, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert claims["sub"] == "kakao:123456789"
    profile = test_client.get(
        "/user/me", headers={"cookie": f"access_token={get_access_token_from_response(response)}"}
    )
    assert profile.status_code == 200
    assert profile.json()["result"] == {"name": "Moa", "provider": "kakao"}

def test_kakao_login_updates_nickname_for_existing_id(client, monkeypatch):
    test_client, test_session = client
    install_kakao_api(monkeypatch, [
        {"id": 123456789, "kakao_account": {"profile": {"nickname": "Moa"}}},
        {"id": 123456789, "kakao_account": {"profile": {"nickname": "Traveler"}}},
    ])
    assert test_client.post("/user/kakao/login", json={"code": "first-code"}).status_code == 200
    response = test_client.post("/user/kakao/login", json={"code": "second-code"})
    assert response.status_code == 200
    from app.models.kakao_account import KakaoAccount
    with test_session() as db:
        account = db.query(KakaoAccount).one()
        assert account.kakao_user_id == "123456789"
        assert account.nickname == "Traveler"


def test_kakao_login_rejects_invalid_code(client, monkeypatch):
    test_client, _ = client
    monkeypatch.setattr(kakao, "KAKAO_REST_API_KEY", "test-rest-api-key")
    def reject_code(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 400, "invalid_grant", {}, None)
    monkeypatch.setattr(kakao, "urlopen", reject_code)
    response = test_client.post("/user/kakao/login", json={"code": "invalid-code"})
    assert response.status_code == 401
    assert response.json()["code"] == 401
    assert response.json()["result"] is None


def test_kakao_login_returns_502_when_kakao_is_unavailable(client, monkeypatch):
    test_client, _ = client
    monkeypatch.setattr(kakao, "KAKAO_REST_API_KEY", "test-rest-api-key")
    def kakao_unavailable(request, timeout=None):
        raise urllib.error.URLError("offline")
    monkeypatch.setattr(kakao, "urlopen", kakao_unavailable)
    response = test_client.post("/user/kakao/login", json={"code": "authorization-code"})
    assert response.status_code == 502
    assert response.json()["code"] == 502
    assert response.json()["result"] is None


def test_kakao_login_returns_502_when_rest_api_key_is_missing(client, monkeypatch):
    test_client, _ = client
    called = False

    def should_not_call_kakao(request, timeout=None):
        nonlocal called
        called = True
        raise AssertionError("Kakao should not be contacted without configuration")

    monkeypatch.setattr(kakao, "KAKAO_REST_API_KEY", "")
    monkeypatch.setattr(kakao, "urlopen", should_not_call_kakao)
    response = test_client.post("/user/kakao/login", json={"code": "authorization-code"})
    assert response.status_code == 502
    assert called is False


def test_kakao_login_rejects_profile_without_nickname(client, monkeypatch):
    test_client, _ = client
    install_kakao_api(monkeypatch, [{"id": 123456789, "kakao_account": {"profile": {}}}])
    response = test_client.post("/user/kakao/login", json={"code": "authorization-code"})
    assert response.status_code == 401


def test_kakao_login_rejects_malformed_profile(client, monkeypatch):
    test_client, _ = client
    install_kakao_api(monkeypatch, [{"id": 123456789, "kakao_account": None}])
    response = test_client.post("/user/kakao/login", json={"code": "authorization-code"})
    assert response.status_code == 401


def test_kakao_login_does_not_store_or_return_email(client, monkeypatch):
    test_client, test_session = client
    install_kakao_api(monkeypatch, [{
        "id": 123456789,
        "kakao_account": {"profile": {"nickname": "Moa"}, "email": "local@example.com"},
    }])
    response = test_client.post("/user/kakao/login", json={"code": "authorization-code"})
    assert response.status_code == 200
    assert "access_token" not in response.text
    assert get_access_token_from_response(response)
    from app.models.kakao_account import KakaoAccount
    with test_session() as db:
        account = db.query(KakaoAccount).one()
        assert not hasattr(account, "email")
        assert db.query(User).count() == 0


class FakeKakaoResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *_args):
        return False
    def read(self):
        return self.body


def install_kakao_api(monkeypatch, profiles):
    monkeypatch.setattr(kakao, "KAKAO_REST_API_KEY", "test-rest-api-key")
    remaining_profiles = list(profiles)
    def fake_urlopen(request, timeout=None):
        if request.full_url == "https://kauth.kakao.com/oauth/token":
            return FakeKakaoResponse({"access_token": "verified-kakao-token"})
        if request.full_url == "https://kapi.kakao.com/v2/user/me":
            return FakeKakaoResponse(remaining_profiles.pop(0))
        raise AssertionError(f"Unexpected Kakao endpoint: {request.full_url}")
    monkeypatch.setattr(kakao, "urlopen", fake_urlopen)


def get_access_token_from_response(response):
    cookies = SimpleCookie()
    cookies.load(response.headers["set-cookie"])
    return cookies["access_token"].value
