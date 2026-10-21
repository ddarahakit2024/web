import axios from 'axios'

export const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000'

function baseUrl(value) {
  return (value || import.meta.env?.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, '')
}

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
