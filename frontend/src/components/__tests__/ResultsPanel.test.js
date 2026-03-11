import { render, screen } from '@testing-library/react'
import ResultsPanel from '../ResultsPanel'

describe('ResultsPanel', () => {
  it('shows idle placeholder when there are no results', () => {
    render(<ResultsPanel results={null} loading={false} error={null} />)
    expect(screen.getByText(/run analysis to see results/i)).toBeInTheDocument()
  })

  it('shows analyzing message while loading', () => {
    render(<ResultsPanel results={null} loading={true} error={null} />)
    expect(screen.getByText(/analyzing/i)).toBeInTheDocument()
  })

  it('shows the error message on failure', () => {
    render(
      <ResultsPanel results={null} loading={false} error="Analysis failed (500)" />
    )
    expect(screen.getByText(/analysis failed \(500\)/i)).toBeInTheDocument()
  })

  it('renders JSON results in a pre element', () => {
    const results = { status: 'received', lines: 42 }
    render(<ResultsPanel results={results} loading={false} error={null} />)
    const pre = screen.getByRole('generic', { hidden: true })
    expect(screen.getByText(/"status": "received"/)).toBeInTheDocument()
    expect(screen.getByText(/"lines": 42/)).toBeInTheDocument()
  })
})
