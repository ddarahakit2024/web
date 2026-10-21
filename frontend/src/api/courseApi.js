import axios from 'axios'
import { baseUrl } from './config.js'

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
