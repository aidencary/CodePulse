const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

// FR-ACCT-001
export async function getProfile(token) {
  const res = await fetch(`${API_URL}/api/v1/account/profile`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error(`Failed to load profile (${res.status})`)
  return res.json()
}

// FR-ACCT-001
export async function updateProfile(token, data) {
  const res = await fetch(`${API_URL}/api/v1/account/profile`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })
  if (res.status === 409) throw new Error('Username already taken')
  if (!res.ok) throw new Error(`Failed to update profile (${res.status})`)
  return res.json()
}

// FR-ACCT-002
export async function uploadAvatar(token, file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_URL}/api/v1/account/avatar`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  })
  if (res.status === 413) throw new Error('File too large. Maximum size is 2 MB')
  if (res.status === 422) throw new Error('Unsupported file type. Use PNG, JPEG, or WebP')
  if (!res.ok) throw new Error(`Failed to upload avatar (${res.status})`)
  return res.json()
}

// FR-ACCT-003
export async function changePassword(token, data) {
  const res = await fetch(`${API_URL}/api/v1/account/change-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })
  if (res.status === 401) throw new Error('Current password is incorrect')
  if (!res.ok) throw new Error(`Failed to change password (${res.status})`)
  return res.json()
}

// FR-ACCT-005
export async function inviteUser(token, email) {
  const res = await fetch(`${API_URL}/api/v1/account/invite`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ email }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || `Failed to send invite (${res.status})`)
  }
  return res.json()
}

// FR-ACCT-004
export async function deleteAccount(token) {
  const res = await fetch(`${API_URL}/api/v1/account`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error(`Failed to delete account (${res.status})`)
  return res.json()
}
