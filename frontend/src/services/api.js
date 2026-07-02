export async function api(path, options = {}) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
  const url = path.startsWith('http') ? path : `${baseUrl}${path}`
  const response = await fetch(url, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.error || 'No se pudo completar la accion.')
  }
  return data
}

export async function currentUser() {
  try {
    const data = await api('/api/auth/me/')
    return data.user
  } catch {
    return null
  }
}
