import { fireEvent, render, screen } from '@testing-library/react'
import ResultsPanel from '../ResultsPanel'

// Shared fixture
const mockResults = {
  overall_score: 72,
  summary: 'Score 72/100 — 2 static findings, 1 predicted bug.',
  findings: [
    {
      issue_type: 'long_line',
      line_number: 5,
      severity: 'Low',
      message: 'Line exceeds 88 characters (95 chars).',
    },
    {
      issue_type: 'bare_except',
      line_number: 12,
      severity: 'Med',
      message: "Bare 'except:' clause catches all exceptions.",
    },
  ],
  predicted_bugs: [
    {
      line_number: 8,
      bug_type: 'null_dereference',
      severity: 'high',
      description: 'Variable may be None when accessed here.',
      suggested_fix: 'Add a None check: if x is not None: ...',
    },
  ],
}

// Idle / error states
describe('ResultsPanel — idle and error states', () => {
  // TC-REPORT-001
  it('shows idle placeholder when there are no results', () => {
    render(<ResultsPanel results={null} loading={false} error={null} />)
    expect(screen.getByText(/run analysis to see/i)).toBeInTheDocument()
  })

  // TC-REPORT-002
  it('shows the error message on failure', () => {
    render(
      <ResultsPanel results={null} loading={false} error="Analysis failed (500)" />
    )
    expect(screen.getByText(/analysis failed \(500\)/i)).toBeInTheDocument()
  })
})

// Loading skeleton
describe('ResultsPanel — loading state', () => {
  // TC-REPORT-003
  it('shows the skeleton with aria-label while loading', () => {
    render(<ResultsPanel results={null} loading={true} error={null} />)
    expect(screen.getByLabelText(/analyzing/i)).toBeInTheDocument()
  })

  // TC-REPORT-004
  it('does not show the skeleton when not loading', () => {
    render(<ResultsPanel results={null} loading={false} error={null} />)
    expect(screen.queryByLabelText(/analyzing/i)).not.toBeInTheDocument()
  })
})

// Score section
describe('ResultsPanel — score section', () => {
  // TC-REPORT-005
  it('displays the overall score', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(screen.getByText('72')).toBeInTheDocument()
  })

  // TC-REPORT-006
  it('displays the summary text', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(screen.getByText(mockResults.summary)).toBeInTheDocument()
  })
})

// Static findings section
describe('ResultsPanel — findings section', () => {
  // TC-REPORT-007
  it('renders each finding type', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(screen.getByText('long_line')).toBeInTheDocument()
    expect(screen.getByText('bare_except')).toBeInTheDocument()
  })

  // TC-REPORT-008
  it('renders finding line numbers', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(screen.getByText('L5')).toBeInTheDocument()
    expect(screen.getByText('L12')).toBeInTheDocument()
  })

  // TC-REPORT-009
  it('renders finding messages', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(
      screen.getByText(/line exceeds 88 characters/i)
    ).toBeInTheDocument()
  })

  // TC-REPORT-010
  it('shows empty state when findings array is empty', () => {
    const emptyResults = { ...mockResults, findings: [] }
    render(<ResultsPanel results={emptyResults} loading={false} error={null} />)
    expect(screen.getByText(/no issues found/i)).toBeInTheDocument()
  })
})

// AI bug predictions section
describe('ResultsPanel — predicted bugs section', () => {
  // TC-REPORT-011
  it('renders the bug type', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(screen.getByText('null_dereference')).toBeInTheDocument()
  })

  // TC-REPORT-012
  it('renders the bug description', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(
      screen.getByText(/variable may be none when accessed here/i)
    ).toBeInTheDocument()
  })

  // TC-REPORT-013
  it('renders the bug line number', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(screen.getByText('L8')).toBeInTheDocument()
  })

  // TC-REPORT-014
  it('does not render line number when bug.line_number is null', () => {
    const noLineResults = {
      ...mockResults,
      predicted_bugs: [{ ...mockResults.predicted_bugs[0], line_number: null }],
    }
    render(<ResultsPanel results={noLineResults} loading={false} error={null} />)
    // L8 should not appear since line_number is null
    expect(screen.queryByText('L8')).not.toBeInTheDocument()
  })

  // TC-REPORT-015
  it('expands suggested fix when toggle is clicked', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    const toggle = screen.getByRole('button', { name: /show suggested fix/i })
    fireEvent.click(toggle)
    expect(
      screen.getByText(/add a none check/i)
    ).toBeInTheDocument()
  })

  // TC-REPORT-016
  it('collapses suggested fix on second click', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    const toggle = screen.getByRole('button', { name: /show suggested fix/i })
    fireEvent.click(toggle)
    fireEvent.click(screen.getByRole('button', { name: /hide fix/i }))
    expect(screen.queryByText(/add a none check/i)).not.toBeInTheDocument()
  })

  // TC-REPORT-017
  it('shows empty state when predicted_bugs array is empty', () => {
    const emptyResults = { ...mockResults, predicted_bugs: [] }
    render(<ResultsPanel results={emptyResults} loading={false} error={null} />)
    expect(screen.getByText(/no predicted bugs found/i)).toBeInTheDocument()
  })
})

// Ignore / dismiss
describe('ResultsPanel — ignore buttons', () => {
  // TC-REPORT-018
  it('ignoring a finding removes it from the list', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    // Default sort is severity desc: bare_except (Med) renders first, long_line (Low) second.
    // Click the first ignore button to dismiss bare_except.
    const ignoreButtons = screen.getAllByTitle('Ignore this finding')
    fireEvent.click(ignoreButtons[0])
    expect(screen.queryByText('bare_except')).not.toBeInTheDocument()
    // long_line (Low) is still present
    expect(screen.getByText('long_line')).toBeInTheDocument()
  })

  // TC-REPORT-019
  it('ignoring a bug removes it from the list', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    fireEvent.click(screen.getByTitle('Ignore this bug'))
    expect(screen.queryByText('null_dereference')).not.toBeInTheDocument()
    expect(screen.getByText(/no predicted bugs found/i)).toBeInTheDocument()
  })

  // TC-REPORT-020
  it('ignored items reappear when results are reset', () => {
    const { rerender } = render(
      <ResultsPanel results={mockResults} loading={false} error={null} />
    )
    // Ignore the first finding (bare_except at index 0 in severity-desc order)
    fireEvent.click(screen.getAllByTitle('Ignore this finding')[0])
    expect(screen.queryByText('bare_except')).not.toBeInTheDocument()

    // Simulate new analysis result (new object reference resets ignore state)
    rerender(
      <ResultsPanel results={{ ...mockResults }} loading={false} error={null} />
    )
    expect(screen.getByText('bare_except')).toBeInTheDocument()
  })
})

// Hover line highlight
describe('ResultsPanel — hover line highlight', () => {
  // TC-REPORT-021
  it('calls onHoverLine with line number when hovering a finding', () => {
    const onHoverLine = jest.fn()
    render(
      <ResultsPanel results={mockResults} loading={false} error={null} onHoverLine={onHoverLine} />
    )
    fireEvent.mouseEnter(screen.getByTestId('finding-long_line'))
    expect(onHoverLine).toHaveBeenCalledWith({ line: 5, severity: 'low' })
  })

  // TC-REPORT-022
  it('calls onHoverLine with null when leaving a finding', () => {
    const onHoverLine = jest.fn()
    render(
      <ResultsPanel results={mockResults} loading={false} error={null} onHoverLine={onHoverLine} />
    )
    fireEvent.mouseLeave(screen.getByTestId('finding-long_line'))
    expect(onHoverLine).toHaveBeenCalledWith(null)
  })

  // TC-REPORT-023
  it('calls onHoverLine with line number when hovering a bug card', () => {
    const onHoverLine = jest.fn()
    render(
      <ResultsPanel results={mockResults} loading={false} error={null} onHoverLine={onHoverLine} />
    )
    fireEvent.mouseEnter(screen.getByTestId('bug-null_dereference'))
    expect(onHoverLine).toHaveBeenCalledWith({ line: 8, severity: 'high' })
  })

  // TC-REPORT-024
  it('does not call onHoverLine when bug has no line number', () => {
    const onHoverLine = jest.fn()
    const noLineResults = {
      ...mockResults,
      predicted_bugs: [{ ...mockResults.predicted_bugs[0], line_number: null }],
    }
    render(
      <ResultsPanel results={noLineResults} loading={false} error={null} onHoverLine={onHoverLine} />
    )
    fireEvent.mouseEnter(screen.getByTestId('bug-null_dereference'))
    expect(onHoverLine).not.toHaveBeenCalledWith(expect.any(Number))
  })
})

// Sort controls
describe('ResultsPanel — sort controls', () => {
  // Three findings: two share severity 'Low' so line-number tiebreaking is testable.
  const sortResults = {
    ...mockResults,
    findings: [
      { issue_type: 'long_line',   line_number: 10, severity: 'Low', message: 'msg-a' },
      { issue_type: 'bare_except', line_number: 2,  severity: 'Med', message: 'msg-b' },
      { issue_type: 'wildcard',    line_number: 7,  severity: 'Low', message: 'msg-c' },
    ],
    predicted_bugs: [
      { line_number: 5,  bug_type: 'alpha', severity: 'high',   description: 'desc-x', suggested_fix: '' },
      { line_number: 1,  bug_type: 'beta',  severity: 'medium', description: 'desc-y', suggested_fix: '' },
    ],
  }

  // TC-REPORT-025
  it('clicking the "Line" pill re-orders findings by line number ascending', () => {
    render(<ResultsPanel results={sortResults} loading={false} error={null} />)
    fireEvent.click(screen.getAllByRole('button', { name: /^Line$/i })[0])
    const lines = screen.getAllByText(/^L\d+$/)
    // First three L-tags belong to findings; they should be L2, L7, L10
    const findingLines = lines.slice(0, 3).map((el) => el.textContent)
    expect(findingLines).toEqual(['L2', 'L7', 'L10'])
  })

  // TC-REPORT-026
  it('direction toggle reverses line sort to descending', () => {
    render(<ResultsPanel results={sortResults} loading={false} error={null} />)
    // Switch to Line sort
    fireEvent.click(screen.getAllByRole('button', { name: /^Line$/i })[0])
    // Flip direction
    fireEvent.click(screen.getAllByRole('button', { name: /low to high/i })[0])
    const lines = screen.getAllByText(/^L\d+$/)
    const findingLines = lines.slice(0, 3).map((el) => el.textContent)
    expect(findingLines).toEqual(['L10', 'L7', 'L2'])
  })

  // TC-REPORT-027
  it('equal-severity findings are tiebroken by line number ascending', () => {
    render(<ResultsPanel results={sortResults} loading={false} error={null} />)
    // Default is Severity desc: Med first, then the two Low findings ordered by line
    const lines = screen.getAllByText(/^L\d+$/)
    const findingLines = lines.slice(0, 3).map((el) => el.textContent)
    // bare_except (Med, L2) first, then Low findings sorted L7 before L10
    expect(findingLines).toEqual(['L2', 'L7', 'L10'])
  })

  // TC-REPORT-028
  it('null line_number findings sort last when Line sort is active', () => {
    const nullLineResults = {
      ...sortResults,
      findings: [
        { issue_type: 'no_line',   line_number: null, severity: 'High', message: 'msg-null' },
        { issue_type: 'has_line',  line_number: 3,    severity: 'Low',  message: 'msg-has' },
        { issue_type: 'also_line', line_number: 1,    severity: 'Med',  message: 'msg-also' },
      ],
    }
    render(<ResultsPanel results={nullLineResults} loading={false} error={null} />)
    fireEvent.click(screen.getAllByRole('button', { name: /^Line$/i })[0])
    // L1 and L3 should appear before the null-line item (which has no L-tag)
    const lines = screen.getAllByText(/^L\d+$/)
    expect(lines[0].textContent).toBe('L1')
    expect(lines[1].textContent).toBe('L3')
    // The null-line finding's issue type still renders, just last
    const items = screen.getAllByText(/msg-null|msg-has|msg-also/)
    expect(items[items.length - 1].textContent).toBe('msg-null')
  })
})

// Download report button
describe('ResultsPanel — download report button', () => {
  // TC-REPORT-029
  it('shows Export button when results are present', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument()
  })

  // TC-REPORT-030
  it('hides Export button when results are null', () => {
    render(<ResultsPanel results={null} loading={false} error={null} />)
    expect(screen.queryByRole('button', { name: /export/i })).not.toBeInTheDocument()
  })

  // TC-REPORT-031
  it('hides Export button during loading', () => {
    render(<ResultsPanel results={null} loading={true} error={null} />)
    expect(screen.queryByRole('button', { name: /export/i })).not.toBeInTheDocument()
  })

  // TC-REPORT-032
  it('creates a Blob with text/html on click', () => {
    global.URL.createObjectURL = jest.fn(() => 'blob:fake')
    global.URL.revokeObjectURL = jest.fn()

    render(<ResultsPanel results={mockResults} loading={false} error={null} submissionName="test.py" />)
    fireEvent.click(screen.getByRole('button', { name: /export/i }))

    expect(global.URL.createObjectURL).toHaveBeenCalled()
    const blob = global.URL.createObjectURL.mock.calls[0][0]
    expect(blob).toBeInstanceOf(Blob)
    expect(blob.type).toBe('text/html')
  })
})

// CodeBERT confidence badge + filter slider
describe('ResultsPanel — CodeBERT confidence', () => {
  const resultsWithConfidence = {
    overall_score: 80,
    summary: 'Score 80/100.',
    findings: [],
    predicted_bugs: [
      {
        line_number: 5,
        bug_type: 'high_conf_bug',
        severity: 'high',
        description: 'desc',
        suggested_fix: 'fix',
        confidence: 0.85,
        flagged: false,
      },
      {
        line_number: 10,
        bug_type: 'low_conf_bug',
        severity: 'low',
        description: 'desc',
        suggested_fix: 'fix',
        confidence: 0.25,
        flagged: true,
      },
    ],
  }

  it('renders a confidence badge for each bug that has a score', () => {
    render(<ResultsPanel results={resultsWithConfidence} loading={false} error={null} />)
    expect(screen.getByText('85%')).toBeInTheDocument()
    expect(screen.getByText('25%')).toBeInTheDocument()
  })

  it('renders no confidence badge for bugs without a score', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(screen.queryByTestId('confidence-badge')).not.toBeInTheDocument()
  })

  it('marks flagged bugs with the flagged class', () => {
    render(<ResultsPanel results={resultsWithConfidence} loading={false} error={null} />)
    const flaggedCard = screen.getByTestId('bug-low_conf_bug')
    expect(flaggedCard.className).toContain('flagged')
  })

  it('hides the slider when no bug has confidence', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(
      screen.queryByLabelText(/minimum codebert confidence/i)
    ).not.toBeInTheDocument()
  })

  it('shows the slider when any bug has confidence', () => {
    render(<ResultsPanel results={resultsWithConfidence} loading={false} error={null} />)
    expect(
      screen.getByLabelText(/minimum codebert confidence/i)
    ).toBeInTheDocument()
  })

  it('filters out bugs below the slider value', () => {
    render(<ResultsPanel results={resultsWithConfidence} loading={false} error={null} />)
    expect(screen.getByTestId('bug-high_conf_bug')).toBeInTheDocument()
    expect(screen.getByTestId('bug-low_conf_bug')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText(/minimum codebert confidence/i), {
      target: { value: '50' },
    })

    expect(screen.getByTestId('bug-high_conf_bug')).toBeInTheDocument()
    expect(screen.queryByTestId('bug-low_conf_bug')).not.toBeInTheDocument()
  })
})
