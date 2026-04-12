import supabase from './supabaseClient'

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

// FR-HIST-001
export async function getSubmissions(userId) {
  const { data, error } = await supabase
    .from('submissions')
    .select('submission_id, name, code, created_at, pinned_at, analysis_reports(overall_score, summary)')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })

  if (error) throw error

  // Sort: pinned first (by pinned_at desc), then unpinned (by created_at desc).
  data.sort((a, b) => {
    const aPinned = a.pinned_at != null
    const bPinned = b.pinned_at != null
    if (aPinned !== bPinned) return bPinned - aPinned
    if (aPinned && bPinned) return b.pinned_at.localeCompare(a.pinned_at)
    return 0 // already sorted by created_at desc from query
  })

  return data
}

export async function getSubmissionDetail(submissionId) {
  const { data, error } = await supabase
    .from('submissions')
    .select(
      'submission_id, name, code, created_at, pinned_at, '
      + 'analysis_reports(overall_score, summary, '
      + 'findings(finding_id, issue_type, line_number, line_severity, message, '
      + 'actionable_fixes(original_snippet, suggested_snippet, rationale, tags)), '
      + 'predicted_bugs(bug_id, bug_type, severity, description, suggested_fix, line_number, confidence, flagged))'
    )
    .eq('submission_id', submissionId)
    .single()

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

// FR-HIST-003
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

// FR-HIST-004
export async function deleteSubmission(submissionId, token) {
  const res = await fetch(`${API_URL}/api/v1/submissions/${submissionId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error(`Failed to delete submission (${res.status})`)
  return res.json()
}

// FR-HIST-005
export async function pinSubmission(submissionId, token) {
  const res = await fetch(`${API_URL}/api/v1/submissions/${submissionId}/pin`, {
    method: 'PATCH',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error(`Failed to pin submission (${res.status})`)
  return res.json()
}
