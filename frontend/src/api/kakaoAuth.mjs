import { baseUrl } from './config.js'

export const KAKAO_STATE_KEY = 'kakao_oauth_state'

async function readApiResult(response) {
  const body = await response.json()
  if (!response.ok) {
    throw new Error(body.message || 'Request failed')
  }
  return body.result
}

export async function postLogin({ fetchImpl = fetch, apiBaseUrl, path, payload }) {
  const response = await fetchImpl(`${baseUrl(apiBaseUrl)}${path}`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return readApiResult(response)
}

export async function fetchCurrentUser({ fetchImpl = fetch, apiBaseUrl } = {}) {
  const response = await fetchImpl(`${baseUrl(apiBaseUrl)}/user/me`, { credentials: 'include' })
  return readApiResult(response)
}

export function redirectToMain(location = window.location) {
  location.assign('/')
}

export function beginKakaoLogin({ sdk, key, redirectUri, storage, state }) {
  if (!sdk || !key || !redirectUri || !state) {
    throw new Error('kakao_not_configured')
  }

  if (!sdk.isInitialized()) {
    sdk.init(key)
  }

  storage.setItem(KAKAO_STATE_KEY, state)
  sdk.Auth.authorize({
    redirectUri,
    scope: 'profile_nickname',
    state,
  })
}

export async function completeKakaoCallback({ search, storage, history, exchangeCode }) {
  const params = new URLSearchParams(search)
  const returnedState = params.get('state')
  const expectedState = storage.getItem(KAKAO_STATE_KEY)
  const code = params.get('code')
  const error = params.get('error')

  storage.removeItem(KAKAO_STATE_KEY)
  history.replaceState({}, '', '/login')

  if (!returnedState || !expectedState || returnedState !== expectedState) {
    return { ok: false, error: 'invalid_state' }
  }
  if (error === 'access_denied') {
    return { ok: false, error: 'cancelled' }
  }
  if (error) {
    return { ok: false, error: 'kakao_error' }
  }
  if (!code) {
    return { ok: false, error: 'missing_code' }
  }

  try {
    await exchangeCode(code)
    return { ok: true }
  } catch {
    return { ok: false, error: 'exchange_failed' }
  }
}
