export function formatCoursePrice(priceKrw) {
  return `₩${Number(priceKrw || 0).toLocaleString('ko-KR')}`
}

export function getCourseImage(course) {
  return course?.thumbnail_url || '/course-placeholder.svg'
}

export function getCourseSummary(course) {
  return course?.summary || '강의 내용을 확인해 보세요.'
}

export function getCourseTitle(course) {
  return course?.title || '제목 없는 강의'
}

export function getCoursePageState({ loading, error = '', missing = false, courses = [], course = null, detail = false }) {
  if (loading) return 'loading'
  if (missing) return 'missing'
  if (error) return 'error'
  if (detail && !course) return 'missing'
  if (course) return 'ready'
  if (courses.length === 0) return 'empty'
  return 'ready'
}

export function getCourseStateView(state, detail = false) {
  const views = {
    loading: { message: detail ? '강의 정보를 불러오는 중입니다...' : '강의를 불러오는 중입니다...', retry: false },
    empty: { message: '등록된 강의가 없습니다.', retry: false },
    error: { message: '강의 정보를 불러오지 못했습니다.', retry: true },
    missing: { message: '강의를 찾을 수 없습니다.', retry: false },
    ready: { message: '', retry: false },
  }
  return views[state] || views.error
}
