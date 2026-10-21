import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.database import Base
from app.main import create_app
from app.models import Course, PaymentOrder, User


@pytest.fixture
def payment_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as db:
        db.add(User(id=1, email="student@example.com", hashed_password="hashed", name="Student"))
        db.add(Course(
            id=1,
            title="FastAPI course",
            instructor_name="MOA Academy",
            category="Backend",
            price_krw=49000,
            thumbnail_url="/course-placeholder.svg",
            summary="Build an API",
            description="A practical course",
            curriculum=[],
            display_order=1,
        ))
        db.commit()
    headers = {"cookie": f"access_token={create_access_token('1')}"}
    with TestClient(create_app(session_factory, create_schema=False)) as test_client:
        yield test_client, session_factory, headers
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def configure_portone(monkeypatch):
    from app.api.routers import payments

    monkeypatch.setattr(payments, "PORTONE_STORE_ID", "store-test")
    monkeypatch.setattr(payments, "PORTONE_CHANNEL_KEY", "channel-key-test")
    monkeypatch.setattr(payments, "PORTONE_API_SECRET", "secret-test")
    return payments


def test_create_order_uses_course_price_and_existing_portone_channel(payment_client, monkeypatch):
    test_client, session_factory, headers = payment_client
    configure_portone(monkeypatch)

    response = test_client.post("/payments/orders", json={"course_id": 1}, headers=headers)

    assert response.status_code == 201
    result = response.json()["result"]
    assert result["payment_id"].startswith("course-")
    assert result["order_name"] == "FastAPI course"
    assert result["total_amount"] == 49000
    assert result["currency"] == "KRW"
    assert result["store_id"] == "store-test"
    assert result["channel_key"] == "channel-key-test"
    with session_factory() as db:
        order = db.get(PaymentOrder, result["payment_id"])
        assert order is not None
        assert order.buyer_subject == "1"
        assert order.amount_krw == 49000
        assert order.status == "READY"


def test_create_order_requires_login(payment_client, monkeypatch):
    test_client, _, _ = payment_client
    configure_portone(monkeypatch)

    response = test_client.post("/payments/orders", json={"course_id": 1})

    assert response.status_code == 401


def test_create_order_fails_closed_when_portone_secret_is_missing(payment_client, monkeypatch):
    test_client, session_factory, headers = payment_client
    payments = configure_portone(monkeypatch)
    monkeypatch.setattr(payments, "PORTONE_API_SECRET", "")

    response = test_client.post("/payments/orders", json={"course_id": 1}, headers=headers)

    assert response.status_code == 503
    with session_factory() as db:
        assert db.query(PaymentOrder).count() == 0


def test_create_order_rejects_unknown_course(payment_client, monkeypatch):
    test_client, _, headers = payment_client
    configure_portone(monkeypatch)

    response = test_client.post("/payments/orders", json={"course_id": 999}, headers=headers)

    assert response.status_code == 404


def test_confirm_marks_order_paid_only_after_portone_verification(payment_client, monkeypatch):
    test_client, session_factory, headers = payment_client
    payments = configure_portone(monkeypatch)
    created = test_client.post("/payments/orders", json={"course_id": 1}, headers=headers)
    payment_id = created.json()["result"]["payment_id"]
    monkeypatch.setattr(payments, "get_portone_payment", lambda requested_id: {
        "id": requested_id,
        "status": "PAID",
        "amount": {"total": 49000},
    })

    response = test_client.post("/payments/confirm", json={"payment_id": payment_id}, headers=headers)

    assert response.status_code == 200
    assert response.json()["result"]["status"] == "PAID"
    with session_factory() as db:
        assert db.get(PaymentOrder, payment_id).status == "PAID"


@pytest.mark.parametrize(
    "payment_response",
    [
        {"status": "READY", "amount": {"total": 49000}},
        {"status": "PAID", "amount": {"total": 1}},
    ],
)
def test_confirm_rejects_unpaid_or_wrong_amount(payment_client, monkeypatch, payment_response):
    test_client, session_factory, headers = payment_client
    payments = configure_portone(monkeypatch)
    created = test_client.post("/payments/orders", json={"course_id": 1}, headers=headers)
    payment_id = created.json()["result"]["payment_id"]
    monkeypatch.setattr(payments, "get_portone_payment", lambda _requested_id: payment_response)

    response = test_client.post("/payments/confirm", json={"payment_id": payment_id}, headers=headers)

    assert response.status_code == 409
    with session_factory() as db:
        assert db.get(PaymentOrder, payment_id).status == "READY"


def test_confirm_does_not_expose_or_accept_another_users_order(payment_client, monkeypatch):
    test_client, session_factory, _ = payment_client
    configure_portone(monkeypatch)
    with session_factory() as db:
        db.add(PaymentOrder(
            payment_id="course-other-user",
            course_id=1,
            buyer_subject="another-user",
            amount_krw=49000,
            status="READY",
        ))
        db.commit()

    response = test_client.post("/payments/confirm", json={"payment_id": "course-other-user"})

    assert response.status_code == 401
