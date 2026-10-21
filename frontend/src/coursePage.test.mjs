import {
  formatCoursePrice,
  getCourseImage,
  getCourseSummary,
  getCoursePageState,
  getCourseStateView,
} from './stores/courseViewModel.js'
import { resolveCourseRoute } from './router/index.js'

const course = {
  id: 7,
  title: 'Vue 입문',
  instructor_name: '김강사',
  category: '프론트엔드',
  price_krw: 120000,
  thumbnail_url: 'https://cdn.example.test/vue.jpg',
  summary: 'Vue로 첫 화면을 만듭니다.',
  description: '상세한 설명',
  curriculum: [{ title: '기초', lessons: ['컴포넌트', '상태'] }],
}

describe('course view model', () => {
  test.each([
    [{ loading: true, courses: [] }, 'loading'],
    [{ loading: false, courses: [] }, 'empty'],
    [{ loading: false, error: 'failed', courses: [] }, 'error'],
    [{ loading: false, missing: true, course: null }, 'missing'],
    [{ loading: false, missing: false, course: null, detail: true }, 'missing'],
    [{ loading: false, course }, 'ready'],
  ])('maps page data to the rendered %s state', (data, expected) => {
    expect(getCoursePageState(data)).toBe(expected)
  })

  test.each([
    ['/', { name: 'catalog' }],
    ['/courses', { name: 'catalog' }],
    ['/courses/7', { name: 'detail', id: 7 }],
    ['/courses/abc', { name: 'detail', id: null }],
    ['/login', { name: 'login' }],
  ])('resolves %s', (path, expected) => expect(resolveCourseRoute(path)).toEqual(expected))

  test('formats API-shaped card/detail values', () => {
    expect(formatCoursePrice(course.price_krw)).toBe('₩120,000')
    expect(getCourseSummary(course)).toBe(course.summary)
    expect(getCourseImage(course)).toBe(course.thumbnail_url)
  })

  test('uses fallback image when thumbnail is absent', () => {
    expect(getCourseImage({ ...course, thumbnail_url: '' })).toBe('/course-placeholder.svg')
  })

  test('keeps retryable error and missing states distinct', () => {
    expect(getCoursePageState({ loading: false, error: 'network', course: null })).toBe('error')
    expect(getCoursePageState({ loading: false, missing: true, course: null })).toBe('missing')
  })

  test('renders state copy and retry affordance for screen conditions', () => {
    expect(getCourseStateView('loading').message).toContain('강의를 불러오는 중')
    expect(getCourseStateView('empty').message).toBe('등록된 강의가 없습니다.')
    expect(getCourseStateView('error').retry).toBe(true)
    expect(getCourseStateView('missing', true).message).toBe('강의를 찾을 수 없습니다.')
    expect(getCourseStateView('ready').message).toBe('')
  })
})
