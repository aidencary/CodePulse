/** Severity rank maps (higher number = more severe). */
export const FINDING_SEV_RANK = { high: 3, med: 2, low: 1 }
export const BUG_SEV_RANK = { critical: 4, high: 3, medium: 2, low: 1 }

export function scoreLevel(score) {
  if (score >= 80) return 'good'
  if (score >= 50) return 'fair'
  return 'poor'
}
