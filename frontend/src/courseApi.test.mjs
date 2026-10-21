import { jest } from '@jest/globals'

const get = jest.fn()
jest.unstable_mockModule('axios', () => ({ default: { get } }))
const { default: axios } = await import('axios')
const { fetchCourse, fetchCourses } = await import('./api/courseApi.js')

describe('course API', () => {
  beforeEach(() => jest.clearAllMocks())

  test('fetches courses from the configured base URL and returns result', async () => {
    get.mockResolvedValue({ data: { code: 200, message: 'ok', result: [{ id: 1 }] } })
    await expect(fetchCourses({ apiBaseUrl: 'https://api.example.test/' })).resolves.toEqual([{ id: 1 }])
    expect(get).toHaveBeenCalledWith('https://api.example.test/courses')
  })

  test('uses the local backend default and extracts course detail', async () => {
    get.mockResolvedValue({ data: { code: 200, message: 'ok', result: { id: 3 } } })
    await expect(fetchCourse(3)).resolves.toEqual({ id: 3 })
    expect(get).toHaveBeenCalledWith('http://127.0.0.1:8000/courses/3')
  })

  test('propagates axios errors', async () => {
    const error = new Error('network')
    get.mockRejectedValue(error)
    await expect(fetchCourses({ apiBaseUrl: 'http://api.test' })).rejects.toBe(error)
  })
})
