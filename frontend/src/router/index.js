export function resolveCourseRoute(pathname = '/') {
  if (pathname === '/login' || pathname.startsWith('/login/')) return { name: 'login' }
  const match = pathname.match(/^\/courses\/([^/]+)\/?$/)
  if (match) {
    const id = /^\d+$/.test(match[1]) ? Number(match[1]) : null
    return { name: 'detail', id }
  }
  return { name: 'catalog' }
}

export function isPaymentCompleteRoute(pathname = '/') {
  return pathname === '/payments/complete'
}
