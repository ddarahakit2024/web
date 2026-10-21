import * as authSession from './api/kakaoAuth.mjs'
import { jest } from '@jest/globals'

const { beginKakaoLogin, completeKakaoCallback } = authSession

function createStorage(initial = {}) {
  const values = new Map(Object.entries(initial))
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  }
}

test('starts Kakao authorization with nickname-only scope and a saved state', () => {
  const storage = createStorage()
  const sdk = {
    isInitialized: () => false,
    init: jest.fn(),
    Auth: { authorize: jest.fn() },
  }

  beginKakaoLogin({
    sdk,
    key: 'javascript-key',
    redirectUri: 'http://localhost:5173/login/kakao/callback',
    storage,
    state: 'one-time-state',
  })

  expect(sdk.init).toHaveBeenCalledWith('javascript-key')
  expect(sdk.Auth.authorize).toHaveBeenCalledWith({
    redirectUri: 'http://localhost:5173/login/kakao/callback',
    scope: 'profile_nickname',
    state: 'one-time-state',
  })
  expect(storage.getItem('kakao_oauth_state')).toBe('one-time-state')
})

test('exchanges the callback code only after matching state and clears the callback URL', async () => {
  const storage = createStorage({ kakao_oauth_state: 'one-time-state' })
  const history = { replaceState: jest.fn() }
  const exchangeCode = jest.fn().mockResolvedValue({ authenticated: true })

  const result = await completeKakaoCallback({
    search: '?code=authorization-code&state=one-time-state',
    storage,
    history,
    exchangeCode,
  })

  expect(result).toEqual({ ok: true })
  expect(exchangeCode).toHaveBeenCalledWith('authorization-code')
  expect(history.replaceState).toHaveBeenCalledWith({}, '', '/login')
  expect(storage.getItem('kakao_oauth_state')).toBeNull()
})

test('provides cookie-backed login and profile requests with credentials included', async () => {
  expect(typeof authSession.postLogin).toBe('function')
  expect(typeof authSession.fetchCurrentUser).toBe('function')
  expect(typeof authSession.redirectToMain).toBe('function')

  const fetchImpl = jest.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ result: { authenticated: true } }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ result: { name: 'Moa', provider: 'kakao' } }) })
  await authSession.postLogin({
    fetchImpl,
    apiBaseUrl: 'http://127.0.0.1:8000',
    path: '/user/login',
    payload: { email: 'person@example.com', password: 'secret' },
  })
  const profile = await authSession.fetchCurrentUser({ fetchImpl, apiBaseUrl: 'http://127.0.0.1:8000' })

  expect(fetchImpl.mock.calls.map(([url, options]) => [url, options.credentials])).toEqual([
    ['http://127.0.0.1:8000/user/login', 'include'],
    ['http://127.0.0.1:8000/user/me', 'include'],
  ])
  expect(profile).toEqual({ name: 'Moa', provider: 'kakao' })

  const location = { assign: jest.fn() }
  authSession.redirectToMain(location)
  expect(location.assign).toHaveBeenCalledWith('/')
})

test.each([
  ['missing', '?code=authorization-code'],
  ['mismatched', '?code=authorization-code&state=other-state'],
])('does not exchange an authorization code when state is %s', async (_reason, search) => {
  const exchangeCode = jest.fn()
  const result = await completeKakaoCallback({
    search,
    storage: createStorage({ kakao_oauth_state: 'one-time-state' }),
    history: { replaceState: jest.fn() },
    exchangeCode,
  })

  expect(result).toEqual({ ok: false, error: 'invalid_state' })
  expect(exchangeCode).not.toHaveBeenCalled()
})

test('reports Kakao cancellation without exchanging a code', async () => {
  const exchangeCode = jest.fn()
  const result = await completeKakaoCallback({
    search: '?error=access_denied&state=one-time-state',
    storage: createStorage({ kakao_oauth_state: 'one-time-state' }),
    history: { replaceState: jest.fn() },
    exchangeCode,
  })

  expect(result).toEqual({ ok: false, error: 'cancelled' })
  expect(exchangeCode).not.toHaveBeenCalled()
})

test('reports a rejected backend code exchange', async () => {
  const result = await completeKakaoCallback({
    search: '?code=authorization-code&state=one-time-state',
    storage: createStorage({ kakao_oauth_state: 'one-time-state' }),
    history: { replaceState: jest.fn() },
    exchangeCode: jest.fn().mockRejectedValue(new Error('invalid code')),
  })

  expect(result).toEqual({ ok: false, error: 'exchange_failed' })
})
