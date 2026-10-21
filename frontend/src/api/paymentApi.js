import axios from 'axios'
import { baseUrl } from './config.js'

function resultOf(response) {
  return response.data.result
}

export async function createPaymentOrder(courseId, { apiBaseUrl } = {}) {
  const response = await axios.post(
    `${baseUrl(apiBaseUrl)}/payments/orders`,
    { course_id: courseId },
    { withCredentials: true },
  )
  return resultOf(response)
}

export async function confirmPayment(paymentId, { apiBaseUrl } = {}) {
  const response = await axios.post(
    `${baseUrl(apiBaseUrl)}/payments/confirm`,
    { payment_id: paymentId },
    { withCredentials: true },
  )
  return resultOf(response)
}
