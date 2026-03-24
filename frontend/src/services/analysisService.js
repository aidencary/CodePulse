const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

/**
 * Send code to the backend analysis endpoint.
 *
 * @param {string} code - The source code string to analyze.
 * @param {string} token - Supabase JWT (session.access_token).
 * @returns {Promise<Object>} Parsed JSON response from the backend.
 * @throws {Error} If the request fails or the server returns a non-2xx status.
 */
export async function analyzeCode(code, token, name, submissionId) {
  const body = { code }
  if (name) body.name = name
  if (submissionId) body.submission_id = submissionId

  const response = await fetch(`${API_URL}/api/v1/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    throw new Error(`Analysis failed (${response.status})`)
  }

  return response.json()
}
