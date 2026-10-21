import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import PORTONE_API_SECRET, PORTONE_CHANNEL_KEY, PORTONE_STORE_ID
from app.core.session import get_current_subject
from app.models import Course, PaymentOrder
from app.schemas.payment import (
    ConfirmPaymentRequest,
    CreatePaymentOrderRequest,
    PaymentOrderResponse,
)

router = APIRouter(prefix="/payments", tags=["payments"])


def get_portone_payment(payment_id: str) -> dict:
    request = urllib.request.Request(
        f"https://api.portone.io/payments/{payment_id}",
        headers={"Authorization": f"PortOne {PORTONE_API_SECRET}"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _require_payment_configuration() -> None:
    if not (PORTONE_STORE_ID and PORTONE_CHANNEL_KEY and PORTONE_API_SECRET):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="결제 연동 설정이 완료되지 않았습니다. 관리자에게 문의해 주세요.",
        )


def _order_result(order: PaymentOrder, course: Course) -> dict:
    return {
        "payment_id": order.payment_id,
        "course_id": course.id,
        "order_name": course.title,
        "total_amount": order.amount_krw,
        "currency": "KRW",
        "store_id": PORTONE_STORE_ID,
        "channel_key": PORTONE_CHANNEL_KEY,
        "status": order.status,
    }


@router.post("/orders", response_model=PaymentOrderResponse, status_code=status.HTTP_201_CREATED)
def create_payment_order(
    payload: CreatePaymentOrderRequest,
    buyer_subject: str = Depends(get_current_subject),
    db: Session = Depends(get_db),
):
    _require_payment_configuration()
    course = db.get(Course, payload.course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="강의를 찾을 수 없습니다.")

    existing = db.query(PaymentOrder).filter(
        PaymentOrder.course_id == course.id,
        PaymentOrder.buyer_subject == buyer_subject,
        PaymentOrder.status == "PAID",
    ).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 구매한 강의입니다.")

    order = PaymentOrder(
        payment_id=f"course-{uuid4().hex}",
        course_id=course.id,
        buyer_subject=buyer_subject,
        amount_krw=course.price_krw,
        status="READY",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return {
        "code": status.HTTP_201_CREATED,
        "message": "결제 주문을 생성했습니다.",
        "result": _order_result(order, course),
    }


@router.post("/confirm", response_model=PaymentOrderResponse)
def confirm_payment(
    payload: ConfirmPaymentRequest,
    buyer_subject: str = Depends(get_current_subject),
    db: Session = Depends(get_db),
):
    _require_payment_configuration()
    order = db.get(PaymentOrder, payload.payment_id)
    if order is None or order.buyer_subject != buyer_subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="결제 주문을 찾을 수 없습니다.")
    course = db.get(Course, order.course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="강의를 찾을 수 없습니다.")
    if order.status == "PAID":
        return {
            "code": status.HTTP_200_OK,
            "message": "결제가 확인되었습니다.",
            "result": _order_result(order, course),
        }

    try:
        payment = get_portone_payment(order.payment_id)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="포트원 결제 정보를 확인하지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from None

    payment_id = payment.get("id") or payment.get("paymentId")
    amount = payment.get("amount")
    if (
        payment_id != order.payment_id
        or payment.get("status") != "PAID"
        or not isinstance(amount, dict)
        or amount.get("total") != order.amount_krw
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="결제가 완료되지 않았거나 결제 금액이 주문과 일치하지 않습니다.",
        )

    order.status = "PAID"
    order.paid_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return {
        "code": status.HTTP_200_OK,
        "message": "결제가 확인되었습니다.",
        "result": _order_result(order, course),
    }
