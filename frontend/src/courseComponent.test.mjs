import axios from 'axios'
import * as Vue from 'vue'
import { createRenderer, nextTick } from 'vue'
import { compileScript, compileTemplate, parse } from '@vue/compiler-sfc'
import { jest } from '@jest/globals'
import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { fetchCourse, fetchCourses } from './api/courseApi.js'
import {
  formatCoursePrice,
  getCourseImage,
  getCoursePageState,
  getCourseStateView,
  getCourseSummary,
  getCourseTitle,
} from './stores/courseViewModel.js'

const sourceRoot = dirname(fileURLToPath(import.meta.url))
const confirmPayment = jest.fn()
const createPaymentOrder = jest.fn()
const launchPortOnePayment = jest.fn()

function hostRenderer() {
  const make = (type, props = {}) => ({ type, props, children: [], text: '', parent: null })
  const renderer = createRenderer({
    patchProp: (node, key, _, value) => { node.props[key] = value },
    insert: (node, parent) => { node.parent = parent; parent.children.push(node) },
    remove: (node) => { if (node.parent) node.parent.children = node.parent.children.filter((child) => child !== node) },
    createElement: (type) => make(type),
    createText: (text) => ({ type: '#text', text, children: [], parent: null }),
    createComment: (text) => ({ type: '#comment', text, children: [], parent: null }),
    setText: (node, text) => { node.text = text },
    setElementText: (node, text) => { node.text = text; node.children = [] },
    insertStaticContent: (content, parent) => { const node = { type: '#static', text: content, children: [], parent }; parent.children.push(node); return [node, node] },
    parentNode: (node) => node.parent,
    nextSibling: () => null,
    querySelector: () => null,
  })
  return { ...renderer, root: make('root') }
}

function textContent(node) { return `${node.text || ''}${node.children.map(textContent).join('')}` }

async function flushVue() {
  await Promise.resolve()
  await nextTick()
  await Promise.resolve()
  await nextTick()
}

function find(node, predicate) {
  if (predicate(node)) return node
  for (const child of node.children) { const found = find(child, predicate); if (found) return found }
  return null
}

function compileClientComponent(filename) {
  const descriptor = parse(readFileSync(filename, 'utf8')).descriptor
  const script = compileScript(descriptor, { id: filename })
  const content = script.content
    .replace(/^import .* from 'vue'\r?\n/gm, '')
    .replace(/^import .* from '\.\.\/api\/courseApi\.js'\r?\n/gm, '')
    .replace(/^import .* from '\.\.\/api\/paymentApi\.js'\r?\n/gm, '')
    .replace(/^import .* from '\.\.\/api\/coursePayment\.js'\r?\n/gm, '')
    .replace(/^import .* from '\.\.\/stores\/courseViewModel\.js'\r?\n/gm, '')
    .replace(/^import \{.*\} from '\.\.\/components\/index\.js'\r?\n/gm, '')
    .replace(/import\.meta\.env\.VITE_API_BASE_URL/g, 'undefined')
    .replace('export default', 'return')
  const CoursePageLayout = { setup(_, { slots }) { return () => Vue.h('main', slots.default?.()) } }
  const CourseSearchBar = { setup() { return () => Vue.h('div') } }
  const CourseGrid = {
    props: ['courses', 'emptyMessage'],
    setup(props) {
      return () => Vue.h('div', (props.courses || []).map((course) => Vue.h('a', { class: 'course-card', href: '/courses/' + course.id }, [
        Vue.h('img', { src: course.thumbnail_url, onError: (event) => { event.target.src = '/course-placeholder.svg' } }),
        Vue.h('h3', course.title),
        Vue.h('p', course.summary),
        Vue.h('strong', '₩' + Number(course.price_krw || 0).toLocaleString('ko-KR')),
      ])))
    },
  }
  const CourseSummary = { props: ['title', 'summary'], setup(props) { return () => Vue.h('section', [Vue.h('h1', props.title), Vue.h('p', props.summary)]) } }
  const CourseGallery = { props: ['images'], setup(props) { return () => Vue.h('div', (props.images || []).map((image) => Vue.h('img', { src: image.src, onError: (event) => { event.target.src = '/course-placeholder.svg' } }))) } }
  const CoursePurchaseCard = { emits: ['purchase'], setup(_, { emit }) { return () => Vue.h('button', { class: 'course-button purchase-button', onClick: () => emit('purchase') }, '강의 구매하기') } }
  const component = new Function(
    'computed', 'onMounted', 'ref', 'fetchCourse', 'fetchCourses', 'confirmPayment', 'createPaymentOrder', 'launchPortOnePayment',
    'formatCoursePrice', 'getCourseImage', 'getCoursePageState', 'getCourseStateView', 'getCourseSummary', 'getCourseTitle',
    'CourseGrid', 'CoursePageLayout', 'CourseSearchBar', 'CourseGallery', 'CoursePurchaseCard', 'CourseSummary',
    content,
  )(
    Vue.computed, Vue.onMounted, Vue.ref,
    fetchCourse, fetchCourses, confirmPayment, createPaymentOrder, launchPortOnePayment,
    formatCoursePrice, getCourseImage, getCoursePageState, getCourseStateView, getCourseSummary, getCourseTitle,
    CourseGrid, CoursePageLayout, CourseSearchBar, CourseGallery, CoursePurchaseCard, CourseSummary,
  )
  const template = compileTemplate({ source: descriptor.template.content, filename, id: filename, compilerOptions: { bindingMetadata: script.bindings, mode: 'function' } })
  component.render = new Function('Vue', template.code)(Vue)
  return component
}

describe('compiled course screens', () => {
  let Catalog
  let Detail
  beforeAll(() => { Catalog = compileClientComponent(resolve(sourceRoot, 'views/CourseCatalog.vue')); Detail = compileClientComponent(resolve(sourceRoot, 'views/CourseDetail.vue')) })
  beforeEach(() => { jest.restoreAllMocks(); confirmPayment.mockReset(); createPaymentOrder.mockReset(); launchPortOnePayment.mockReset() })

  test('catalog renders loading then empty', async () => {
    let resolveRequest
    jest.spyOn(axios, 'get').mockReturnValue(new Promise((resolve) => { resolveRequest = resolve }))
    const mounted = hostRenderer(); const app = mounted.createApp(Catalog); app.mount(mounted.root)
    await nextTick(); expect(textContent(mounted.root)).toContain('강의를 불러오는 중입니다...')
    resolveRequest({ data: { result: [] } }); await flushVue()
    expect(textContent(mounted.root)).toContain('등록된 강의가 없습니다.')
  })

  test('catalog renders a populated API course and image fallback', async () => {
    jest.spyOn(axios, 'get').mockResolvedValue({ data: { result: [{ id: 4, title: 'React 실전', instructor_name: '강사', category: '웹', price_krw: 45000, thumbnail_url: '/thumb.jpg', summary: '실전 강의' }] } })
    const mounted = hostRenderer(); mounted.createApp(Catalog).mount(mounted.root)
    await flushVue()
    expect(textContent(mounted.root)).toContain('React 실전')
    expect(textContent(mounted.root)).toContain('₩45,000')
    expect(find(mounted.root, (node) => node.type === 'a' && node.props.class === 'course-card' && node.props.href === '/courses/4')).toBeTruthy()
    const image = find(mounted.root, (node) => node.type === 'img')
    image.props.onError({ target: image.props })
    expect(image.props.src).toBe('/course-placeholder.svg')
  })

  test('detail error retry renders ready course', async () => {
    const get = jest.spyOn(axios, 'get').mockRejectedValueOnce(new Error('network')).mockResolvedValueOnce({ data: { result: { id: 1, title: 'Vue 입문', category: '웹', instructor_name: '강사', price_krw: 1000, summary: '요약', description: '설명', curriculum: [] } } })
    const mounted = hostRenderer(); const app = mounted.createApp(Detail, { courseId: 1 }); app.mount(mounted.root)
    await flushVue()
    expect(textContent(mounted.root)).toContain('강의 정보를 불러오지 못했습니다.')
    const button = find(mounted.root, (node) => node.type === 'button' && node.text === '다시 시도')
    const retry = Object.values(button?.props || {}).find((value) => typeof value === 'function')
    if (!retry) throw new Error(`retry handler missing: root=${textContent(mounted.root)} button=${JSON.stringify(button)}`)
    retry()
    await flushVue()
    expect(get).toHaveBeenCalledTimes(2); expect(textContent(mounted.root)).toContain('Vue 입문')
    expect(textContent(mounted.root)).not.toContain('수강 신청하기')
  })

  test('detail 404 renders recovery link and ready image fallback', async () => {
    jest.spyOn(axios, 'get').mockRejectedValue({ response: { status: 404 } })
    const mounted = hostRenderer(); mounted.createApp(Detail, { courseId: 9 }).mount(mounted.root)
    await flushVue()
    expect(textContent(mounted.root)).toContain('강의를 찾을 수 없습니다.')
    expect(find(mounted.root, (node) => node.type === 'a' && node.props.href === '/courses')).toBeTruthy()

    const readyAxios = jest.spyOn(axios, 'get')
    readyAxios.mockResolvedValue({ data: { result: { id: 9, title: '강의', instructor_name: '강사', category: '웹', price_krw: 1000, thumbnail_url: '/detail.jpg', summary: '요약', description: '설명', curriculum: [] } } })
    const ready = hostRenderer(); ready.createApp(Detail, { courseId: 9 }).mount(ready.root)
    await flushVue()
    const image = find(ready.root, (node) => node.type === 'img')
    image.props.onError({ target: image.props })
    expect(image.props.src).toBe('/course-placeholder.svg')
  })

  test('detail invalid id renders a recovery state without requesting the API', async () => {
    const get = jest.spyOn(axios, 'get')
    const mounted = hostRenderer(); mounted.createApp(Detail, { courseId: null }).mount(mounted.root)
    await flushVue()
    expect(textContent(mounted.root)).toContain('올바르지 않은 강의 ID입니다.')
    expect(find(mounted.root, (node) => node.type === 'a' && node.props.href === '/courses')).toBeTruthy()
    expect(get).not.toHaveBeenCalled()
  })

  test('detail starts PortOne checkout and confirms payment on the server', async () => {
    jest.spyOn(axios, 'get').mockResolvedValue({ data: { result: { id: 4, title: 'FastAPI', category: 'Backend', instructor_name: 'MOA Academy', price_krw: 49000, thumbnail_url: '/course.svg', summary: 'API', description: 'Course', curriculum: [] } } })
    const order = { payment_id: 'course-test', total_amount: 49000 }
    createPaymentOrder.mockResolvedValue(order)
    launchPortOnePayment.mockResolvedValue(undefined)
    confirmPayment.mockResolvedValue({ status: 'PAID' })
    const mounted = hostRenderer(); mounted.createApp(Detail, { courseId: 4 }).mount(mounted.root)
    await flushVue()

    const button = find(mounted.root, (node) => node.type === 'button' && node.props.class === 'course-button purchase-button')
    await button.props.onClick()
    await flushVue()

    expect(createPaymentOrder).toHaveBeenCalledWith(4, { apiBaseUrl: undefined })
    expect(launchPortOnePayment).toHaveBeenCalledWith(order)
    expect(confirmPayment).toHaveBeenCalledWith('course-test', { apiBaseUrl: undefined })
    expect(textContent(mounted.root)).toContain('구매가 완료되었습니다.')
  })

  test('detail directs unauthenticated learners to login', async () => {
    jest.spyOn(axios, 'get').mockResolvedValue({ data: { result: { id: 4, title: 'FastAPI', category: 'Backend', instructor_name: 'MOA Academy', price_krw: 49000, thumbnail_url: '/course.svg', summary: 'API', description: 'Course', curriculum: [] } } })
    createPaymentOrder.mockRejectedValue({ response: { status: 401, data: { message: 'Authentication required.' } } })
    const mounted = hostRenderer(); mounted.createApp(Detail, { courseId: 4 }).mount(mounted.root)
    await flushVue()
    const button = find(mounted.root, (node) => node.type === 'button' && node.props.class === 'course-button purchase-button')
    await button.props.onClick()
    await flushVue()

    expect(textContent(mounted.root)).toContain('로그인 후 강의를 구매할 수 있습니다.')
    expect(find(mounted.root, (node) => node.type === 'a' && node.props.href === '/login')).toBeTruthy()
    expect(launchPortOnePayment).not.toHaveBeenCalled()
  })
})
