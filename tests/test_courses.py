import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.main import create_app
from app.models import Course


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with TestClient(create_app(session, create_schema=False)) as test_client:
        yield test_client, session
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def course(**overrides):
    values = {
        "title": "FastAPI 입문",
        "instructor_name": "홍길동",
        "category": "백엔드",
        "price_krw": 55000,
        "thumbnail_url": "https://example.com/fastapi.png",
        "summary": "FastAPI로 API를 만듭니다.",
        "description": "실전 예제로 배우는 FastAPI 강의입니다.",
        "curriculum": [{"title": "기초", "lessons": ["설치", "라우팅"]}],
        "display_order": 1,
    }
    values.update(overrides)
    return Course(**values)


def test_courses_returns_empty_list(client):
    response = client[0].get("/courses")
    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["result"] == []


def test_courses_list_is_ordered_and_contains_list_fields(client):
    test_client, session = client
    with session() as db:
        db.add_all([
            course(title="둘", display_order=2),
            course(title="셋", display_order=1),
            course(title="넷", display_order=1),
        ])
        db.commit()

    response = test_client.get("/courses")
    assert response.status_code == 200
    result = response.json()["result"]
    assert [item["title"] for item in result] == ["셋", "넷", "둘"]
    assert set(result[0]) == {
        "id", "title", "instructor_name", "category", "price_krw", "thumbnail_url", "summary"
    }


def test_course_detail_contains_curriculum_and_description(client):
    test_client, session = client
    with session() as db:
        item = course()
        db.add(item)
        db.commit()
        course_id = item.id

    response = test_client.get(f"/courses/{course_id}")
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["id"] == course_id
    assert result["description"] == "실전 예제로 배우는 FastAPI 강의입니다."
    assert result["curriculum"] == [{"title": "기초", "lessons": ["설치", "라우팅"]}]


def test_missing_course_returns_404_envelope(client):
    response = client[0].get("/courses/999")
    assert response.status_code == 404
    assert response.json()["code"] == 404
    assert response.json()["result"] is None


def test_non_numeric_course_id_returns_422_envelope(client):
    response = client[0].get("/courses/not-a-number")
    assert response.status_code == 422
    assert response.json() == {
        "code": 422,
        "message": "요청 값이 올바르지 않습니다.",
        "result": None,
    }
