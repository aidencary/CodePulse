import supabase from './supabaseClient'

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

export async function getSubmissions(userId) {
  const { data, error } = await supabase
    .from('submissions')
    .select('submission_id, name, code, created_at, analysis_reports(overall_score, summary)')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })

  if (error) throw error
  return data
}

export async function saveSubmission(userId, code) {
  const { data, error } = await supabase
    .from('submissions')
    .insert({ user_id: userId, code })
    .select()
    .single()

  if (error) throw error
  return data
}

export async function renameSubmission(submissionId, name, token) {
  const res = await fetch(`${API_URL}/api/v1/submissions/${submissionId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error(`Failed to rename submission (${res.status})`)
  return res.json()
}

export async function deleteSubmission(submissionId, token) {
  const res = await fetch(`${API_URL}/api/v1/submissions/${submissionId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error(`Failed to delete submission (${res.status})`)
  return res.json()
}
