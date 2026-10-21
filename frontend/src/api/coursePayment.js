import * as PortOne from '@portone/browser-sdk/v2'

export function createPortOnePaymentRequest(order, origin = window.location.origin) {
  return {
    storeId: order.store_id,
    channelKey: order.channel_key,
    paymentId: order.payment_id,
    orderName: order.order_name,
    totalAmount: order.total_amount,
    currency: 'KRW',
    payMethod: 'CARD',
    locale: 'KO_KR',
    redirectUrl: new URL('/payments/complete', origin).toString(),
  }
}

export async function launchPortOnePayment(order) {
  return PortOne.requestPayment(createPortOnePaymentRequest(order))
}

