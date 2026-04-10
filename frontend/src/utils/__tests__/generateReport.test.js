import generateReportHTML from '../generateReport'

const mockResults = {
  overall_score: 72,
  summary: 'Score 72/100 — 2 static findings, 1 predicted bug.',
  findings: [
    { issue_type: 'long_line', line_number: 5, severity: 'Low', message: 'Line exceeds 88 characters.' },
    { issue_type: 'bare_except', line_number: 12, severity: 'High', message: 'Bare except clause.' },
  ],
  predicted_bugs: [
    {
      line_number: 8,
      bug_type: 'null_dereference',
      severity: 'high',
      description: 'Variable may be None.',
      suggested_fix: 'if x is not None: ...',
    },
  ],
}

describe('generateReportHTML', () => {
  // TC-RPT-GEN-001
  it('includes score, summary, findings, and bugs in output', () => {
    const html = generateReportHTML(mockResults, 'test.py')
    expect(html).toContain('72')
    expect(html).toContain('Score 72/100')
    expect(html).toContain('long_line')
    expect(html).toContain('bare_except')
    expect(html).toContain('Line exceeds 88 characters.')
    expect(html).toContain('null_dereference')
    expect(html).toContain('Variable may be None.')
    expect(html).toContain('if x is not None: ...')
  })

  // TC-RPT-GEN-002
  it('uses green color for score >= 80', () => {
    const html = generateReportHTML({ ...mockResults, overall_score: 90 }, 'good.py')
    expect(html).toContain('#16a34a')
  })

  // TC-RPT-GEN-003
  it('uses yellow color for score 50-79', () => {
    const html = generateReportHTML({ ...mockResults, overall_score: 65 }, 'fair.py')
    expect(html).toContain('#ca8a04')
  })

  // TC-RPT-GEN-004
  it('uses red color for score < 50', () => {
    const html = generateReportHTML({ ...mockResults, overall_score: 30 }, 'poor.py')
    expect(html).toContain('#dc2626')
  })

  // TC-RPT-GEN-005
  it('escapes HTML in user-provided strings to prevent XSS', () => {
    const xssResults = {
      ...mockResults,
      findings: [
        { issue_type: 'xss', line_number: 1, severity: 'High', message: '<script>alert("xss")</script>' },
      ],
    }
    const html = generateReportHTML(xssResults, 'xss.py')
    expect(html).toContain('&lt;script&gt;')
    expect(html).not.toContain('<script>alert')
  })

  // TC-RPT-GEN-006
  it('handles empty findings array gracefully', () => {
    const html = generateReportHTML({ ...mockResults, findings: [] }, 'empty.py')
    expect(html).toContain('No issues found.')
    expect(html).toContain('Static Analysis Findings (0)')
  })

  // TC-RPT-GEN-007
  it('handles empty predicted_bugs array gracefully', () => {
    const html = generateReportHTML({ ...mockResults, predicted_bugs: [] }, 'empty.py')
    expect(html).toContain('No predicted bugs.')
    expect(html).toContain('AI Bug Predictions (0)')
  })

  // TC-RPT-GEN-008
  it('includes submission name in the title and header', () => {
    const html = generateReportHTML(mockResults, 'my_script.py')
    expect(html).toContain('my_script.py')
    expect(html).toContain('<title>CodePulse Report')
  })

  // TC-RPT-GEN-009
  it('uses "Untitled" when no submission name is provided', () => {
    const html = generateReportHTML(mockResults, null)
    expect(html).toContain('Untitled')
  })

  // TC-RPT-GEN-010
  it('is a complete HTML document', () => {
    const html = generateReportHTML(mockResults, 'test.py')
    expect(html).toMatch(/^<!DOCTYPE html>/)
    expect(html).toContain('<html')
    expect(html).toContain('</html>')
    expect(html).toContain('<style>')
  })
})
