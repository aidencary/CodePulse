/**
 * Results panel that displays the analysis output from the backend.
 *
 * @param {Object} props
 * @param {Object|null} props.results - Parsed JSON response from the backend.
 * @param {boolean} props.loading - True while the API request is in flight.
 * @param {string|null} props.error - Error message to display on failure.
 */
function ResultsPanel({ results, loading, error }) {
  const renderContent = () => {
    if (loading) {
      return <p className="results-placeholder">Analyzing…</p>
    }
    if (error) {
      return <p className="results-error">{error}</p>
    }
    if (results) {
      return (
        <pre className="results-pre">{JSON.stringify(results, null, 2)}</pre>
      )
    }
    return (
      <p className="results-placeholder">Run analysis to see results.</p>
    )
  }

  return (
    <div className="results-panel">
      <div className="panel-header">
        <h2 className="panel-title">Results</h2>
      </div>
      <div className="results-body">
        {renderContent()}
      </div>
    </div>
  )
}

export default ResultsPanel
