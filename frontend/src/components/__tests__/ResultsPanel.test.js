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
  it('shows idle placeholder when there are no results', () => {
    render(<ResultsPanel results={null} loading={false} error={null} />)
    expect(screen.getByText(/run analysis to see results/i)).toBeInTheDocument()
  })

  it('shows the error message on failure', () => {
    render(
      <ResultsPanel results={null} loading={false} error="Analysis failed (500)" />
    )
    expect(screen.getByText(/analysis failed \(500\)/i)).toBeInTheDocument()
  })
})

// Loading skeleton
describe('ResultsPanel — loading state', () => {
  it('shows the skeleton with aria-label while loading', () => {
    render(<ResultsPanel results={null} loading={true} error={null} />)
    expect(screen.getByLabelText(/analyzing/i)).toBeInTheDocument()
  })

  it('does not show the skeleton when not loading', () => {
    render(<ResultsPanel results={null} loading={false} error={null} />)
    expect(screen.queryByLabelText(/analyzing/i)).not.toBeInTheDocument()
  })
})

// Score section
describe('ResultsPanel — score section', () => {
  it('displays the overall score', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(screen.getByText('72')).toBeInTheDocument()
  })

  it('displays the summary text', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(screen.getByText(mockResults.summary)).toBeInTheDocument()
  })
})

// Static findings section
describe('ResultsPanel — findings section', () => {
  it('renders each finding type', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(screen.getByText('long_line')).toBeInTheDocument()
    expect(screen.getByText('bare_except')).toBeInTheDocument()
  })

  it('renders finding line numbers', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(screen.getByText('L5')).toBeInTheDocument()
    expect(screen.getByText('L12')).toBeInTheDocument()
  })

  it('renders finding messages', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(
      screen.getByText(/line exceeds 88 characters/i)
    ).toBeInTheDocument()
  })

  it('shows empty state when findings array is empty', () => {
    const emptyResults = { ...mockResults, findings: [] }
    render(<ResultsPanel results={emptyResults} loading={false} error={null} />)
    expect(screen.getByText(/no issues found/i)).toBeInTheDocument()
  })
})

// AI bug predictions section
describe('ResultsPanel — predicted bugs section', () => {
  it('renders the bug type', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(screen.getByText('null_dereference')).toBeInTheDocument()
  })

  it('renders the bug description', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(
      screen.getByText(/variable may be none when accessed here/i)
    ).toBeInTheDocument()
  })

  it('renders the bug line number', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    expect(screen.getByText('L8')).toBeInTheDocument()
  })

  it('does not render line number when bug.line_number is null', () => {
    const noLineResults = {
      ...mockResults,
      predicted_bugs: [{ ...mockResults.predicted_bugs[0], line_number: null }],
    }
    render(<ResultsPanel results={noLineResults} loading={false} error={null} />)
    // L8 should not appear since line_number is null
    expect(screen.queryByText('L8')).not.toBeInTheDocument()
  })

  it('expands suggested fix when toggle is clicked', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    const toggle = screen.getByRole('button', { name: /show suggested fix/i })
    fireEvent.click(toggle)
    expect(
      screen.getByText(/add a none check/i)
    ).toBeInTheDocument()
  })

  it('collapses suggested fix on second click', () => {
    render(<ResultsPanel results={mockResults} loading={false} error={null} />)
    const toggle = screen.getByRole('button', { name: /show suggested fix/i })
    fireEvent.click(toggle)
    fireEvent.click(screen.getByRole('button', { name: /hide fix/i }))
    expect(screen.queryByText(/add a none check/i)).not.toBeInTheDocument()
  })

  it('shows empty state when predicted_bugs array is empty', () => {
    const emptyResults = { ...mockResults, predicted_bugs: [] }
    render(<ResultsPanel results={emptyResults} loading={false} error={null} />)
    expect(screen.getByText(/no predicted bugs found/i)).toBeInTheDocument()
  })
})
