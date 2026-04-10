import { FINDING_SEV_RANK, BUG_SEV_RANK, scoreLevel } from './scoreHelpers'

function escapeHTML(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const SCORE_COLORS = { good: '#16a34a', fair: '#ca8a04', poor: '#dc2626' }

const FINDING_SEV_COLORS = { high: '#b91c1c', med: '#a16207', low: '#15803d' }
const FINDING_SEV_BG = { high: '#fef2f2', med: '#fefce8', low: '#f0fdf4' }

const BUG_SEV_COLORS = { critical: '#7e22ce', high: '#b91c1c', medium: '#a16207', low: '#15803d' }
const BUG_SEV_BG = { critical: '#faf5ff', high: '#fef2f2', medium: '#fefce8', low: '#f0fdf4' }

export default function generateReportHTML(results, submissionName) {
  const name = submissionName || 'Untitled'
  const level = scoreLevel(results.overall_score)
  const scoreColor = SCORE_COLORS[level]
  const timestamp = new Date().toLocaleString()

  const sortedFindings = [...(results.findings || [])].sort((a, b) => {
    const diff = (FINDING_SEV_RANK[b.severity.toLowerCase()] || 0) - (FINDING_SEV_RANK[a.severity.toLowerCase()] || 0)
    if (diff !== 0) return diff
    return (a.line_number || 0) - (b.line_number || 0)
  })

  const sortedBugs = [...(results.predicted_bugs || [])].sort((a, b) => {
    const diff = (BUG_SEV_RANK[b.severity.toLowerCase()] || 0) - (BUG_SEV_RANK[a.severity.toLowerCase()] || 0)
    if (diff !== 0) return diff
    return (a.line_number || 0) - (b.line_number || 0)
  })

  const findingsRows = sortedFindings.length === 0
    ? '<tr><td colspan="4" style="text-align:center;color:#6b7280;padding:1.5rem;">No issues found.</td></tr>'
    : sortedFindings.map((f) => {
        const sev = f.severity.toLowerCase()
        const color = FINDING_SEV_COLORS[sev] || '#6b7280'
        const bg = FINDING_SEV_BG[sev] || '#f9fafb'
        return `<tr>
          <td><span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:600;color:${color};background:${bg};">${escapeHTML(f.severity)}</span></td>
          <td style="font-weight:500;">${escapeHTML(f.issue_type)}</td>
          <td style="text-align:center;">${f.line_number != null ? f.line_number : '—'}</td>
          <td>${escapeHTML(f.message)}</td>
        </tr>`
      }).join('\n')

  const bugCards = sortedBugs.length === 0
    ? '<p style="text-align:center;color:#6b7280;padding:1.5rem 0;">No predicted bugs.</p>'
    : sortedBugs.map((b) => {
        const sev = b.severity.toLowerCase()
        const color = BUG_SEV_COLORS[sev] || '#6b7280'
        const bg = BUG_SEV_BG[sev] || '#f9fafb'
        return `<div style="border:1px solid #e5e7eb;border-radius:8px;padding:1rem;margin-bottom:0.75rem;">
          <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
            <span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:600;color:${color};background:${bg};">${escapeHTML(b.severity)}</span>
            <strong>${escapeHTML(b.bug_type)}</strong>
            ${b.line_number != null ? `<span style="color:#6b7280;font-size:0.85rem;">Line ${b.line_number}</span>` : ''}
          </div>
          <p style="margin:0 0 0.5rem;color:#374151;line-height:1.5;">${escapeHTML(b.description)}</p>
          <div style="background:#f3f4f6;border-radius:6px;padding:0.75rem;"><strong style="font-size:0.8rem;color:#6b7280;">Suggested Fix</strong><pre style="margin:0.4rem 0 0;white-space:pre-wrap;font-size:0.85rem;color:#1f2937;">${escapeHTML(b.suggested_fix)}</pre></div>
        </div>`
      }).join('\n')

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CodePulse Report — ${escapeHTML(name)}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1f2937; background: #ffffff; line-height: 1.6; }
  .header { background: #7c3aed; color: #fff; padding: 1.5rem 2rem; }
  .header h1 { font-size: 1.4rem; font-weight: 700; }
  .header .sub { font-size: 0.85rem; opacity: 0.85; margin-top: 0.25rem; }
  .container { max-width: 800px; margin: 0 auto; padding: 1.5rem; }
  .score-card { display: flex; align-items: center; gap: 1.25rem; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 10px; padding: 1.25rem; margin-bottom: 1.5rem; }
  .score-num { font-size: 2.5rem; font-weight: 800; line-height: 1; }
  .score-max { font-size: 1rem; font-weight: 400; color: #9ca3af; }
  .score-summary { color: #4b5563; font-size: 0.95rem; }
  h2 { font-size: 1.1rem; font-weight: 700; margin-bottom: 0.75rem; color: #7c3aed; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 1.5rem; }
  th { text-align: left; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #6b7280; padding: 0.5rem; border-bottom: 2px solid #e5e7eb; }
  td { padding: 0.6rem 0.5rem; border-bottom: 1px solid #f3f4f6; font-size: 0.88rem; vertical-align: top; }
  .footer { text-align: center; color: #9ca3af; font-size: 0.78rem; padding: 2rem 0 1rem; border-top: 1px solid #e5e7eb; margin-top: 1.5rem; }
  @media print {
    .header { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    body { font-size: 11pt; }
  }
</style>
</head>
<body>
<div class="header">
  <h1>CodePulse Analysis Report</h1>
  <div class="sub">${escapeHTML(name)} &mdash; ${escapeHTML(timestamp)}</div>
</div>
<div class="container">
  <div class="score-card">
    <div><span class="score-num" style="color:${scoreColor};">${results.overall_score}</span><span class="score-max"> / 100</span></div>
    <p class="score-summary">${escapeHTML(results.summary)}</p>
  </div>

  <h2>Static Analysis Findings (${sortedFindings.length})</h2>
  <table>
    <thead><tr><th>Severity</th><th>Issue Type</th><th style="text-align:center;">Line</th><th>Message</th></tr></thead>
    <tbody>${findingsRows}</tbody>
  </table>

  <h2>AI Bug Predictions (${sortedBugs.length})</h2>
  ${bugCards}

  <div class="footer">Generated by CodePulse on ${escapeHTML(timestamp)}</div>
</div>
</body>
</html>`
}
