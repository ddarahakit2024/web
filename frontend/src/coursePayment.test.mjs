import { createPortOnePaymentRequest } from './api/coursePayment.js'

test('builds a V2 Toss payment request with the existing PortOne channel', () => {
  expect(createPortOnePaymentRequest({
    store_id: 'store-test',
    channel_key: 'channel-key-test',
    payment_id: 'course-123',
    order_name: 'FastAPI course',
    total_amount: 49000,
  }, 'http://127.0.0.1:5173')).toEqual({
    storeId: 'store-test',
    channelKey: 'channel-key-test',
    paymentId: 'course-123',
    orderName: 'FastAPI course',
    totalAmount: 49000,
    currency: 'KRW',
    payMethod: 'CARD',
    locale: 'KO_KR',
    redirectUrl: 'http://127.0.0.1:5173/payments/complete',
  })
})
