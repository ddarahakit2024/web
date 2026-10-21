import axios from 'axios'

export const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000'

function baseUrl(value) {
  return (value || import.meta.env?.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, '')
}

function resultOf(response) {
  return response.data.result
}

export async function fetchCourses({ apiBaseUrl } = {}) {
  const response = await axios.get(`${baseUrl(apiBaseUrl)}/courses`)
  return resultOf(response)
}

export async function fetchCourse(courseId, { apiBaseUrl } = {}) {
  const response = await axios.get(`${baseUrl(apiBaseUrl)}/courses/${encodeURIComponent(courseId)}`)
  return resultOf(response)
}
