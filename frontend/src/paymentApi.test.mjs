import axios from 'axios'
import { jest } from '@jest/globals'

const { confirmPayment, createPaymentOrder } = await import('./api/paymentApi.js')

afterEach(() => jest.restoreAllMocks())

test('creates an authenticated order using the configured API base URL', async () => {
  const post = jest.spyOn(axios, 'post').mockResolvedValue({ data: { result: { payment_id: 'course-1' } } })

  await expect(createPaymentOrder(7, { apiBaseUrl: 'http://127.0.0.1:8000/' })).resolves.toEqual({ payment_id: 'course-1' })

  expect(post).toHaveBeenCalledWith('http://127.0.0.1:8000/payments/orders', { course_id: 7 }, { withCredentials: true })
})

test('confirms a payment with the authenticated session cookie', async () => {
  const post = jest.spyOn(axios, 'post').mockResolvedValue({ data: { result: { status: 'PAID' } } })

  await expect(confirmPayment('course-1')).resolves.toEqual({ status: 'PAID' })

  expect(post).toHaveBeenCalledWith('http://127.0.0.1:8000/payments/confirm', { payment_id: 'course-1' }, { withCredentials: true })
})
