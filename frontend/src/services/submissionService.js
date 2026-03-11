import supabase from './supabaseClient'

export async function getSubmissions(userId) {
  const { data, error } = await supabase
    .from('submissions')
    .select('submission_id, code, created_at, analysis_reports(overall_score, summary)')
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
