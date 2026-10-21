from pydantic import BaseModel, Field


class CreatePaymentOrderRequest(BaseModel):
    course_id: int = Field(gt=0)


class ConfirmPaymentRequest(BaseModel):
    payment_id: str = Field(min_length=1, max_length=100)


class PaymentOrderResult(BaseModel):
    payment_id: str
    course_id: int
    order_name: str
    total_amount: int
    currency: str = "KRW"
    store_id: str
    channel_key: str
    status: str


class PaymentOrderResponse(BaseModel):
    code: int
    message: str
    result: PaymentOrderResult
